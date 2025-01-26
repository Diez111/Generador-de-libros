from datetime import datetime
from collections import deque, defaultdict
from models.content_rating import ContentRating

class StoryManager:
    def __init__(self):
        self.context = {
            "meta": {
                "titulo": "",
                "autor": "",
                "tema": "",
                "genero": "Ficción",
                "subgenero": "",
                "fecha": datetime.now(),
                "idioma": "es"
            },
            "mundo": {
                "elementos": [],
                "sistema": "",
                "tecnologia": "",
                "sociedad": ""
            },
            "estado": {
                "personajes": {},
                "lugares": {},
                "linea_tiempo": [],
                "cap_actual": 0,
                "total_caps": 0,
                "rating": ContentRating.PG.value,
                "estilo": {
                    "dialogos": "guiones",
                    "descripcion": 3,
                    "ritmo": "moderado",
                    "long_cap": "normal"
                },
                "trama": {}
            },
            "versiones": deque(maxlen=5),
            "historial_caps": []
        }
    
    def actualizar_estado(self, nuevo: dict, cap: int) -> list:
        conflictos = []
        
        for p, datos in nuevo.get('personajes', {}).items():
            if p in self.context['estado']['personajes']:
                actual = self.context['estado']['personajes'][p]
                for k, v in datos.items():
                    if k in actual and actual[k] != v:
                        conflictos.append(f"Conflicto en {p}: {k} (era: {actual[k]}, nuevo: {v})")
                    actual[k] = v
            else:
                self.context['estado']['personajes'][p] = datos
        
        for l, datos in nuevo.get('lugares', {}).items():
            lugar = self.context['estado']['lugares'].setdefault(l, {
                'historial': [],
                'actual': {}
            })
            lugar['historial'].append({
                'capitulo': cap,
                'detalles': datos
            })
            lugar['actual'].update(datos)
        
        if 'eventos' in nuevo:
            self.context['estado']['linea_tiempo'].append({
                "capitulo": cap,
                "eventos": nuevo['eventos']
            })
        
        return conflictos