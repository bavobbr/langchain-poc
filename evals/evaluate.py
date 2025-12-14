
import sys
import os
import json
import time
from typing import List, Dict

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from evals.adapters import BotAdapter, RAGBotAdapter, MockBotAdapter
from langchain_google_vertexai import VertexAI
from logger import get_logger

logger = get_logger(__name__)

class BotEvaluator:
    def __init__(self, bot_adapter: BotAdapter):
        self.bot = bot_adapter
        self.judge_llm = VertexAI(
            model_name=config.LLM_MODEL,
            project=config.PROJECT_ID,
            location=config.REGION,
            temperature=0 # Zero temp for consistent grading
        )

    def evaluate_dataset(self, dataset_path: str = "evals/generated_dataset.json"):
        """Run the evaluation loop."""
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset not found: {dataset_path}")
            return

        with open(dataset_path, "r") as f:
            dataset = json.load(f)
            
        logger.info(f"Starting evaluation of {len(dataset)} items...")
        
        results = []
        score_sum = 0
        
        for i, item in enumerate(dataset):
            question = item["question"]
            ground_truth = item["ground_truth"]
            variant = item.get("variant", "indoor")
            
            logger.info(f"Evaluating Q{i+1}: {question[:50]}...")
            
            # 1. Get Bot Answer via Adapter
            try:
                response = self.bot.query(question)
                bot_answer = response.get("answer", "")
            except Exception as e:
                logger.error(f"Bot failed to answer: {e}")
                bot_answer = "ERROR"
                response = {}
            
            # 2. Check Retrieval Hit Rate
            # We check if the source_text (if present) is found in the retrieved docs
            source_text = item.get("source_text")
            is_hit = False
            if source_text:
                for doc in response.get("source_docs", []):
                    if doc.page_content == source_text:
                        is_hit = True
                        break
            
            # 3. Grade Answer
            score, reasoning = self._grade_answer(question, ground_truth, bot_answer)
            score_sum += score
            
            logger.info(f"  -> Score: {score}/1. Hit: {is_hit}. Reason: {reasoning[:50]}...")
            
            results.append({
                "question": question,
                "ground_truth": ground_truth,
                "bot_answer": bot_answer,
                "score": score,
                "retrieval_hit": is_hit if source_text else None,
                "reasoning": reasoning
            })
            
            # Rate limit politeness
            time.sleep(1)
            
        accuracy = (score_sum / len(dataset)) * 100
        
        # Calculate Hit Rate (only for items that had source_text)
        items_with_source = [r for r in results if r["retrieval_hit"] is not None]
        hit_rate = 0.0
        if items_with_source:
            hits = sum(1 for r in items_with_source if r["retrieval_hit"])
            hit_rate = (hits / len(items_with_source)) * 100
            
        logger.info(f"Evaluation Complete. Accuracy: {accuracy:.2f}%. Retrieval Hit Rate: {hit_rate:.2f}%")
        
        # Save detailed report
        report_path = "evals/report_latest.json"
        with open(report_path, "w") as f:
            json.dump({
                "accuracy": accuracy,
                "hit_rate": hit_rate,
                "details": results
            }, f, indent=2)
            
        return accuracy

    def _grade_answer(self, question, ground_truth, bot_answer):
        """Asks LLM to judge the answer."""
        prompt = f"""
        You are a strict teacher grading an exam.
        
        Question: {question}
        
        Ground Truth Answer: {ground_truth}
        
        Student Answer: {bot_answer}
        
        INSTRUCTIONS:
        1. Compare the Student Answer to the Ground Truth.
        2. If the Student Answer contains the correct key facts, grade it 1.
        3. If it is missing key facts or is wrong, grade it 0.
        4. Ignore minor phrasing differences.
        
        FORMAT:
        Output JSON only: {{"score": 1, "reasoning": "..."}}
        """
        
        try:
            response = self.judge_llm.invoke(prompt).strip()
            response = response.replace("```json", "").replace("```", "")
            grade = json.loads(response)
            return grade.get("score", 0), grade.get("reasoning", "Parse Error")
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            return 0, "Grading Failed"

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Evaluation on a specific Bot implementation.")
    parser.add_argument("--bot", type=str, default="rag", choices=["rag", "mock"], help="Which bot adapter to use.")
    args = parser.parse_args()
    
    if args.bot == "mock":
        adapter = MockBotAdapter()
    else:
        adapter = RAGBotAdapter()
        
    evaluator = BotEvaluator(adapter)
    evaluator.evaluate_dataset()
