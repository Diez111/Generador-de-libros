import regex
import json
from collections import defaultdict

class CoherenceAnalyzer:
    def __init__(self):
        self.entity_tracker = defaultdict(dict)
        self.relationship_graph = defaultdict(set)
        self.timeline_events = []
    
    def update_entities(self, content: str, chapter: int):
        entities = self.extract_entities(content)
        for entity, details in entities.items():
            if entity not in self.entity_tracker:
                self.entity_tracker[entity] = {
                    'type': None,
                    'history': [],
                    'last_chapter': None
                }
            self.entity_tracker[entity]['type'] = details['type']
            self.entity_tracker[entity]['history'].append({
                'chapter': chapter,
                'details': details
            })
            self.entity_tracker[entity]['last_chapter'] = chapter
    
    def extract_entities(self, text: str) -> dict:
        entities = {}
        enhanced_pattern = r"""
            (?i)(?P<name>[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)
            \s+
            (?P<type>(personaje|lugar|objeto|evento))
            \s*:\s*
            (?P<details>\{.*?\})
            (?=\s+[A-ZÁÉÍÓÚ]|\Z)
        """
        matches = regex.finditer(enhanced_pattern, text, regex.DOTALL | regex.VERBOSE)
        
        for match in matches:
            try:
                details_str = match.group('details').replace("'", '"')
                details = json.loads(details_str)
                entities[match.group('name')] = {
                    'type': match.group('type'),
                    'details': details
                }
            except (json.JSONDecodeError, KeyError):
                continue
        return entities
    
    def validate_continuity(self, new_content: dict, chapter: int) -> list:
        errors = []
        current_entities = self.extract_entities(new_content)
        
        for entity, details in current_entities.items():
            if entity not in self.entity_tracker:
                continue
                
            tracker = self.entity_tracker[entity]
            
            if tracker['type'] and tracker['type'] != details['type']:
                errors.append(f"Tipo inconsistente para {entity} (era {tracker['type']}, ahora {details['type']})")
            
            if details['type'] == 'personaje' and 'estado' in details['details']:
                prev_state = next(
                    (e['details'].get('estado') for e in reversed(tracker['history']) 
                     if e['chapter'] < chapter and 'estado' in e['details']),
                    None
                )
                if prev_state and details['details']['estado'] != prev_state:
                    errors.append(f"Estado inconsistente para {entity}: {prev_state} → {details['details']['estado']}")
            
            if details['type'] == 'lugar' and 'ubicacion' in details['details']:
                if tracker['history']:
                    last_location = tracker['history'][-1]['details'].get('ubicacion')
                    if last_location and details['details']['ubicacion'] != last_location:
                        errors.append(f"Ubicación inconsistente para {entity}: {last_location} → {details['details']['ubicacion']}")
        
        return errors