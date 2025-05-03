"""
Quiz generation module for AI Tutor application.
Generates quizzes based on lesson content.
"""
import re
import json
import random
from typing import Dict, List, Any, Tuple

class QuizGenerator:
    """
    Generates quizzes based on lesson content for the AI Tutor application.
    """
    
    def __init__(self):
        """Initialize the quiz generator."""
        pass
    
    def generate_quiz(self, content: str, title: str, num_questions: int = 5) -> Dict:
        """
        Generate a quiz based on the provided content.
        
        Args:
            content: Text content to base the quiz on
            title: Title for the quiz
            num_questions: Number of questions to generate (default: 5)
            
        Returns:
            Dictionary containing quiz information and questions
        """
        # Preprocess the content
        processed_content = self._preprocess_content(content)
        
        # Identify key concepts and facts
        key_facts = self._extract_key_facts(processed_content)
        
        # Generate questions
        questions = []
        
        # Determine how many of each question type to create
        num_multiple_choice = max(1, int(num_questions * 0.6))  # At least 60% multiple choice
        num_short_answer = num_questions - num_multiple_choice
        
        # Generate multiple choice questions
        for _ in range(num_multiple_choice):
            if key_facts:
                fact = random.choice(key_facts)
                key_facts.remove(fact)  # Avoid reusing the same fact
                question = self._generate_multiple_choice_question(fact, processed_content)
                if question:
                    questions.append(question)
        
        # Generate short answer questions
        for _ in range(num_short_answer):
            if key_facts:
                fact = random.choice(key_facts)
                key_facts.remove(fact)  # Avoid reusing the same fact
                question = self._generate_short_answer_question(fact)
                if question:
                    questions.append(question)
        
        # If we don't have enough questions, generate generic ones
        while len(questions) < num_questions:
            if len(questions) % 2 == 0:
                question = self._generate_generic_multiple_choice_question(processed_content)
            else:
                question = self._generate_generic_short_answer_question(processed_content)
            
            if question:
                questions.append(question)
        
        # Shuffle questions
        random.shuffle(questions)
        
        # Create quiz dictionary
        quiz = {
            "title": title,
            "source_material": content[:500] + "..." if len(content) > 500 else content,
            "questions": questions[:num_questions]  # Ensure we only return the requested number
        }
        
        return quiz
    
    def _preprocess_content(self, content: str) -> str:
        """
        Preprocess the content for question generation.
        
        Args:
            content: Raw text content
            
        Returns:
            Preprocessed content
        """
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters
        content = re.sub(r'[^\w\s.,;:?!()-]', '', content)
        
        return content.strip()
    
    def _extract_key_facts(self, content: str) -> List[str]:
        """
        Extract key facts from the content.
        
        Args:
            content: Preprocessed text content
            
        Returns:
            List of key facts
        """
        # Split into sentences
        sentences = re.split(r'[.!?]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Filter for sentences that are likely to contain facts
        fact_sentences = []
        for sentence in sentences:
            # Look for sentences with indicators of facts
            if (re.search(r'\b(is|are|was|were|has|have|had|can|could|will|would|should|may|might)\b', sentence) and
                not re.search(r'\b(I|we|you)\b', sentence.lower())):
                fact_sentences.append(sentence)
        
        # If we don't have enough fact sentences, use regular sentences
        if len(fact_sentences) < 10:
            # Add some regular sentences, prioritizing longer ones
            regular_sentences = sorted([s for s in sentences if s not in fact_sentences], 
                                      key=len, reverse=True)
            fact_sentences.extend(regular_sentences[:10 - len(fact_sentences)])
        
        return fact_sentences
    
    def _generate_multiple_choice_question(self, fact: str, content: str) -> Dict:
        """
        Generate a multiple choice question based on a key fact.
        
        Args:
            fact: The fact to base the question on
            content: Full preprocessed content for context
            
        Returns:
            Dictionary containing question information
        """
        # Extract key terms from the fact
        words = fact.split()
        key_terms = [w for w in words if len(w) > 4 and w.lower() not in 
                    ['about', 'after', 'again', 'below', 'could', 'every', 
                     'first', 'found', 'great', 'house', 'large', 'learn', 
                     'never', 'other', 'place', 'plant', 'point', 'right', 
                     'small', 'sound', 'spell', 'still', 'study', 'their', 
                     'there', 'these', 'thing', 'think', 'three', 'water', 
                     'where', 'which', 'world', 'would', 'write']]
        
        if not key_terms:
            return None
        
        # Select a term to ask about
        target_term = random.choice(key_terms)
        
        # Create the question by replacing the term with a blank
        question_text = fact.replace(target_term, "________")
        
        # The correct answer is the target term
        correct_answer = target_term
        
        # Generate distractors (wrong answers)
        distractors = self._generate_distractors(target_term, content, 3)
        
        # Create options including the correct answer
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        return {
            "question_text": question_text,
            "question_type": "multiple_choice",
            "correct_answer": correct_answer,
            "options": json.dumps(options)
        }
    
    def _generate_distractors(self, correct_answer: str, content: str, num_distractors: int) -> List[str]:
        """
        Generate plausible wrong answers for a multiple choice question.
        
        Args:
            correct_answer: The correct answer
            content: Full preprocessed content for context
            num_distractors: Number of distractors to generate
            
        Returns:
            List of distractor options
        """
        # Extract words of similar length to the correct answer
        words = re.findall(r'\b\w+\b', content)
        similar_words = [w for w in words if abs(len(w) - len(correct_answer)) <= 2 
                        and w.lower() != correct_answer.lower()
                        and len(w) > 3]
        
        # Remove duplicates and convert to lowercase
        similar_words = list(set([w.lower() for w in similar_words]))
        
        # If we don't have enough similar words, add some generic distractors
        generic_distractors = ["option", "example", "factor", "element", "component", 
                              "feature", "aspect", "quality", "property", "attribute"]
        
        # Select distractors
        if len(similar_words) >= num_distractors:
            return random.sample(similar_words, num_distractors)
        else:
            result = similar_words + random.sample(generic_distractors, 
                                                 num_distractors - len(similar_words))
            return result[:num_distractors]
    
    def _generate_short_answer_question(self, fact: str) -> Dict:
        """
        Generate a short answer question based on a key fact.
        
        Args:
            fact: The fact to base the question on
            
        Returns:
            Dictionary containing question information
        """
        # Convert the fact into a question
        question_text = self._convert_to_question(fact)
        
        # The correct answer is the original fact (simplified)
        correct_answer = fact
        
        return {
            "question_text": question_text,
            "question_type": "short_answer",
            "correct_answer": correct_answer,
            "options": None
        }
    
    def _convert_to_question(self, statement: str) -> str:
        """
        Convert a statement into a question.
        
        Args:
            statement: Statement to convert
            
        Returns:
            Question form of the statement
        """
        statement = statement.strip()
        
        # Check for common patterns and convert to questions
        if re.match(r'.+ is .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) is (.+)', r'What is \1?', statement, flags=re.IGNORECASE)
        elif re.match(r'.+ are .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) are (.+)', r'What are \1?', statement, flags=re.IGNORECASE)
        elif re.match(r'.+ was .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) was (.+)', r'What was \1?', statement, flags=re.IGNORECASE)
        elif re.match(r'.+ were .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) were (.+)', r'What were \1?', statement, flags=re.IGNORECASE)
        elif re.match(r'.+ has .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) has (.+)', r'What does \1 have?', statement, flags=re.IGNORECASE)
        elif re.match(r'.+ have .+', statement, re.IGNORECASE):
            question = re.sub(r'(.+) have (.+)', r'What do \1 have?', statement, flags=re.IGNORECASE)
        else:
            # Generic question formation
            question = f"Explain the following concept: {statement}"
        
        return question
    
    def _generate_generic_multiple_choice_question(self, content: str) -> Dict:
        """
        Generate a generic multiple choice question when specific facts are unavailable.
        
        Args:
            content: Preprocessed text content
            
        Returns:
            Dictionary containing question information
        """
        # Extract some sentences
        sentences = re.split(r'[.!?]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return None
        
        # Select a random sentence
        sentence = random.choice(sentences)
        
        # Extract key terms from the sentence
        words = sentence.split()
        key_terms = [w for w in words if len(w) > 4 and w.isalpha()]
        
        if not key_terms:
            return None
        
        # Select a term to ask about
        target_term = random.choice(key_terms)
        
        # Create the question
        question_text = f"Which of the following terms is mentioned in the context of: '{sentence.replace(target_term, '________')}'?"
        
        # The correct answer is the target term
        correct_answer = target_term
        
        # Generate distractors
        distractors = self._generate_distractors(target_term, content, 3)
        
        # Create options including the correct answer
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        return {
            "question_text": question_text,
            "question_type": "multiple_choice",
            "correct_answer": correct_answer,
            "options": json.dumps(options)
        }
    
    def _generate_generic_short_answer_question(self, content: str) -> Dict:
        """
        Generate a generic short answer question when specific facts are unavailable.
        
        Args:
            content: Preprocessed text content
            
        Returns:
            Dictionary containing question information
        """
        # Extract some sentences
        sentences = re.split(r'[.!?]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return None
        
        # Select a random sentence
        sentence = random.choice(sentences)
        
        # Create a generic question
        question_types = [
            f"Explain what is meant by: '{sentence}'",
            f"What is the significance of: '{sentence}'",
            f"Summarize the meaning of: '{sentence}'",
            f"What concept is described in: '{sentence}'",
            f"Describe the importance of: '{sentence}'"
        ]
        
        question_text = random.choice(question_types)
        
        return {
            "question_text": question_text,
            "question_type": "short_answer",
            "correct_answer": sentence,
            "options": None
        }
