import logging
import spacy
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found")
            self.nlp = None
        
        # Custom entity patterns
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(\+?(\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4})\b',
            "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
            "date": r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        }

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        
        # Pattern-based extraction
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        # spaCy NER if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ not in entities:
                        entities[ent.label_] = []
                    entities[ent.label_].append(ent.text)
            except Exception as e:
                logger.error(f"spaCy NER failed: {str(e)}")
        
        return entities