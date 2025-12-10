
import sys
import os
import json
import time
from typing import List, Dict

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from rag_engine import FIHRulesEngine
from langchain_google_vertexai import VertexAI
from logger import get_logger

logger = get_logger(__name__)

class RAGEvaluator:
    def __init__(self):
        self.engine = FIHRulesEngine()
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
            
            # 1. Get Bot Answer
            # We bypass the history/chat wrapper and Query directly
            # Engine signature: query(user_input, history=[])
            response = self.engine.query(question, history=[])
            bot_answer = response["answer"]
            
            # 2. Grade It
            score, reasoning = self._grade_answer(question, ground_truth, bot_answer)
            score_sum += score
            
            logger.info(f"  -> Score: {score}/1. Reason: {reasoning[:50]}...")
            
            results.append({
                "question": question,
                "ground_truth": ground_truth,
                "bot_answer": bot_answer,
                "score": score,
                "reasoning": reasoning
            })
            
            # Rate limit politeness
            time.sleep(1)
            
        accuracy = (score_sum / len(dataset)) * 100
        logger.info(f"Evaluation Complete. Accuracy: {accuracy:.2f}%")
        
        # Save detailed report
        report_path = "evals/report_latest.json"
        with open(report_path, "w") as f:
            json.dump({
                "accuracy": accuracy,
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

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    evaluator.evaluate_dataset()
