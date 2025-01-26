import json
import os
import signal
import time
import hashlib
import regex
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

from core.coherence_analyzer import CoherenceAnalyzer
from core.api_handler import AdvancedAPIHandler
from core.story_manager import StoryManager
from models.content_rating import ContentRating
from models.encoder import EnhancedJSONEncoder
from utils.document_generator import DocumentGenerator

class ProfessionalNovelGenerator:
    def __init__(self):
        self.config = self.cargar_config()
        self.api = AdvancedAPIHandler(self.config['API_KEY'])
        self.historia = StoryManager()
        self.coherence = CoherenceAnalyzer()
        self.setup_signal()
        self.archivo_backup = "backup_emergencia.pro"
    
    def cargar_config(self) -> Dict:
        config_default = {
            'API_KEY': 'sk-1121ac129e3e4c42a1476979ec965d76',
            'MAX_REINTENTOS': 5,
            'TIMEOUT': 90,
            'AUTO_GUARDADO': True,
            'MIN_PALABRAS': 1800,
            'MAX_CAPS': 40,
            'PROFUNDIDAD_CONTEXTO': 3,
            'MAX_INTENTOS_TRAMA': 7
        }
        
        try:
            with open('config.json') as f:
                user_config = json.load(f)
                return {**config_default, **user_config}
        except FileNotFoundError:
            return config_default
        except json.JSONDecodeError:
            print("⚠️ Configuración inválida, usando valores por defecto")
            return config_default

    def setup_signal(self):
        signal.signal(signal.SIGINT, self.manejar_interrupcion)
        signal.signal(signal.SIGTERM, self.manejar_interrupcion)

    def manejar_interrupcion(self, signum, frame):
        print("\n⚠️ Guardar y salir? [s/n]: ", end="", flush=True)
        respuesta = input().lower()
        if respuesta == 's':
            self.guardar_estado()
            print("💾 Progreso guardado.")
            exit(0)
        else:
            print("▶ Continuando...")

    def guardar_estado(self, emergencia=False):
        estado = {
            "hash": hashlib.sha256(json.dumps(self.historia.context, cls=EnhancedJSONEncoder).encode()).hexdigest(),
            "timestamp": datetime.now().isoformat(),
            "contexto": self.historia.context
        }
        
        nombre = self.archivo_backup if emergencia else f"{self.nombre_seguro(self.historia.context['meta']['titulo'])}.pro"
        
        try:
            with open(nombre, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2, cls=EnhancedJSONEncoder)
            print(f"✅ Guardado: {os.path.abspath(nombre)}")
        except Exception as e:
            print(f"❌ Error al guardar: {str(e)}")

    def cargar_backup(self, archivo: str) -> bool:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                backup = json.load(f)
                
                backup_str = json.dumps(backup['contexto'], ensure_ascii=False, separators=(',', ':'))
                current_hash = hashlib.sha256(backup_str.encode()).hexdigest()
                
                if backup.get('hash') == current_hash:
                    self.historia.context = backup['contexto']
                    print(f"✅ Backup cargado correctamente (Capítulo {self.historia.context['estado']['cap_actual']})")
                    return True
                else:
                    print("❌ El backup está corrupto (hash no coincide)")
                    return False
        except Exception as e:
            print(f"❌ Error cargando backup: {str(e)}")
            return False

    def nombre_seguro(self, texto: str) -> str:
        return regex.sub(r'[\\/*?:"<>|]', "", texto)[:45].strip()

    def configurar_meta(self):
        print("\n" + "═"*80 + "\n📚 Configuración\n" + "═"*80)
        meta = self.historia.context['meta']
        meta['titulo'] = self.validar_input("Título: ", 3, 100)
        meta['autor'] = self.validar_input("Autor: ", 2, 100)
        meta['tema'] = self.validar_input("Tema central: ", 5, 200)
        self.analizar_tema()

    def validar_input(self, prompt: str, min_len: int, max_len: int) -> str:
        while True:
            res = input(prompt).strip()
            if min_len <= len(res) <= max_len:
                return res
            print(f"❌ Debe tener entre {min_len}-{max_len} caracteres.")

    def analizar_tema(self):
        print("\n🔍 Analizando tema...")
        tema = self.historia.context['meta']['tema']
        prompt = f"""Analiza este tema literario y genera:
- Género principal
- Subgénero
- 5 elementos clave
- Nivel tecnológico
- Estructura social

Tema: {tema}

Respuesta JSON con: "genero", "subgenero", "elementos" (lista), 
"sistema", "tecnologia", "sociedad" """
        
        try:
            respuesta = self.api.query(prompt, max_tokens=1200)
            datos = self.api.safe_json_extract(respuesta)
            
            if datos:
                self.historia.context['meta'].update({
                    'genero': datos.get('genero', 'Ficción'),
                    'subgenero': datos.get('subgenero', '')
                })
                self.historia.context['mundo'].update({
                    'elementos': datos.get('elementos', []),
                    'sistema': datos.get('sistema', 'N/A'),
                    'tecnologia': datos.get('tecnologia', 'Medio'),
                    'sociedad': datos.get('sociedad', 'Jerárquica')
                })
            else:
                self.config_default_mundo()
        except Exception as e:
            print(f"⚠️ Error analizando tema: {str(e)}")
            self.config_default_mundo()

    def config_default_mundo(self):
        self.historia.context['mundo'] = {
            'elementos': ['Conflicto central', 'Personajes complejos', 'Mundo detallado'],
            'sistema': 'N/A',
            'tecnologia': 'Medio',
            'sociedad': 'Jerárquica'
        }

    def seleccionar_modo(self):
        print("\n🔧 Modo:")
        print("1. Automático")
        print("2. Manual")
        
        while True:
            opc = input("Opción [1-2]: ").strip()
            if opc in ['1', '2']:
                return opc
            print("❌ Opción inválida")

    def modo_auto(self):
        print("\n" + "═"*80 + "\n🤖 Modo Automático\n" + "═"*80)
        self.config_rating()
        self.config_estilo()
        self.generar_elementos()
        self.generar_trama()
        self.generar_contenido()

    def modo_manual(self):
        print("\n" + "═"*80 + "\n🛠️ Modo Manual\n" + "═"*80)
        self.config_rating()
        self.config_estilo()
        self.manual_personajes()
        self.manual_lugares()
        self.manual_trama()
        self.generar_contenido()

    def config_rating(self):
        print("\n🔞 Rating de contenido:")
        print("1. PG (Todo público)")
        print("2. PG-13 (Mayores de 13)")
        print("3. R (Adultos)")
        
        ratings = {'1': ContentRating.PG.value, '2': ContentRating.PG13.value, '3': ContentRating.R.value}
        while True:
            opc = input("Opción [1-3]: ").strip()
            if opc in ratings:
                self.historia.context['estado']['rating'] = ratings[opc]
                break
            print("❌ Selección inválida")

    def config_estilo(self):
        print("\n🎨 Configuración de estilo:")
        estilo = self.historia.context['estado']['estilo']
        
        estilo['descripcion'] = self.input_num(
            "Nivel descriptivo [1-5] (3): ",
            1, 5, 3
        )
        
        estilo['dialogos'] = self.validar_opcion(
            "Formato de diálogos [guiones/comillas/teatral] (guiones): ",
            ['guiones', 'comillas', 'teatral'],
            'guiones'
        )
        
        estilo['ritmo'] = self.validar_opcion(
            "Ritmo narrativo [rápido/moderado/lento] (moderado): ",
            ['rápido', 'moderado', 'lento'],
            'moderado'
        )
        
        estilo['long_cap'] = self.validar_opcion(
            "Longitud de capítulos [corto/normal/extenso] (normal): ",
            ['corto', 'normal', 'extenso'],
            'normal'
        )

    def input_num(self, prompt: str, min_v: int, max_v: int, default: int) -> int:
        while True:
            try:
                entrada = input(prompt).strip()
                valor = int(entrada) if entrada else default
                if min_v <= valor <= max_v:
                    return valor
                print(f"❌ Debe estar entre {min_v}-{max_v}")
            except ValueError:
                print("❌ Ingrese un número válido")

    def validar_opcion(self, prompt: str, opciones: list, default: str) -> str:
        while True:
            opc = input(prompt).strip().lower() or default
            if opc in opciones:
                return opc
            print(f"❌ Opciones válidas: {', '.join(opciones)}")

    def generar_elementos(self):
        print("\n🧠 Generando elementos narrativos...")
        self.generar_personajes()
        self.generar_lugares()
        self.generar_temas()

    def generar_personajes(self):
        mundo = self.historia.context['mundo']
        prompt = f"""Crea 3-5 personajes principales para {self.historia.context['meta']['genero']}.
Elementos clave: {', '.join(mundo['elementos'])}
Sistema: {mundo['sistema']}
Tecnología: {mundo['tecnologia']}
Sociedad: {mundo['sociedad']}

Formato JSON con:
{{
    "personajes": [
        {{
            "nombre": str,
            "rol": str,
            "motivacion": str,
            "relaciones": str,
            "rasgo": str,
            "arco": str
        }}
    ]
}}"""
        
        try:
            res = self.api.query(prompt, max_tokens=1300)
            datos = self.api.safe_json_extract(res)
            
            if datos and 'personajes' in datos:
                for p in datos['personajes']:
                    self.historia.actualizar_estado({
                        'personajes': {
                            p['nombre']: {
                                'rol': p.get('rol', ''),
                                'motivacion': p.get('motivacion', ''),
                                'relaciones': p.get('relaciones', ''),
                                'rasgo': p.get('rasgo', ''),
                                'arco': p.get('arco', '')
                            }
                        }
                    }, 0)
        except Exception as e:
            print(f"⚠️ Error generando personajes: {str(e)}")

    def generar_lugares(self):
        mundo = self.historia.context['mundo']
        prompt = f"""Crea ubicaciones clave para {self.historia.context['meta']['genero']}.
Elementos clave: {', '.join(mundo['elementos'])}

Formato JSON con:
{{
    "lugares": [
        {{
            "nombre": str,
            "tipo": str,
            "caracteristica": str,
            "importancia": str,
            "historia": str
        }}
    ]
}}"""
        
        try:
            res = self.api.query(prompt, max_tokens=1000)
            datos = self.api.safe_json_extract(res)
            
            if datos and 'lugares' in datos:
                for l in datos['lugares']:
                    self.historia.actualizar_estado({
                        'lugares': {
                            l['nombre']: {
                                'tipo': l.get('tipo', ''),
                                'caracteristica': l.get('caracteristica', ''),
                                'importancia': l.get('importancia', ''),
                                'historia': l.get('historia', '')
                            }
                        }
                    }, 0)
        except Exception as e:
            print(f"⚠️ Error generando lugares: {str(e)}")

    def generar_temas(self):
        prompt = f"""Genera 3-5 temas secundarios para: {self.historia.context['meta']['tema']}
Género: {self.historia.context['meta']['genero']}

Formato JSON con clave "temas" (lista)"""
        
        try:
            res = self.api.query(prompt, max_tokens=500)
            datos = self.api.safe_json_extract(res)
            
            if datos and 'temas' in datos:
                self.historia.context['estado']['temas'] = datos['temas'][:5]
        except Exception as e:
            print(f"⚠️ Error generando temas: {str(e)}")

    def generar_trama(self):
        print("\n📜 Generando estructura de la trama...")
        total_caps = self.input_num("\n✍️ Número de capítulos: ", 1, self.config['MAX_CAPS'], 5)
        
        intentos = 0
        max_intentos = self.config['MAX_INTENTOS_TRAMA']
        while intentos < max_intentos:
            try:
                print(f"\n🔄 Intento {intentos+1}/{max_intentos}")
                mundo = self.historia.context['mundo']
                prompt = f"""Crea una estructura narrativa detallada para {total_caps} capítulos siguiendo ESTRICTAMENTE este formato:
```json
{{
    "capitulos": [
        {{
            "num": 1,
            "titulo": "Título descriptivo",
            "objetivo": "Objetivo narrativo",
            "personajes": ["Personaje1", "Personaje2"],
            "ubicacion": "Ubicación principal",
            "eventos": ["Evento1", "Evento2"],
            "elementos": ["Elemento1", "Elemento2"]
        }}
    ]
}}
```
**Reglas estrictas**:
1. Solo incluir el JSON válido
2. Exactamente {total_caps} capítulos
3. Numeración consecutiva desde 1
4. Campos requeridos en cada capítulo: num, titulo, objetivo, personajes, ubicacion, eventos, elementos

**Contexto**:
- Tema: {self.historia.context['meta']['tema']}
- Género: {self.historia.context['meta']['genero']}
- Elementos: {', '.join(mundo['elementos'])}
- Sistema: {mundo['sistema']}
- Tecnología: {mundo['tecnologia']}"""

                res = self.api.query(prompt, max_tokens=2500, temp=0.3)
                
                # Limpiar y validar respuesta
                res = regex.sub(r'^.*?\{', '{', res, flags=regex.DOTALL)
                datos = self.api.safe_json_extract(res)
                
                if not datos:
                    raise ValueError("Respuesta no contiene JSON válido")
                
                if 'capitulos' not in datos:
                    raise ValueError("Estructura inválida: falta 'capitulos'")
                
                if len(datos['capitulos']) != total_caps:
                    raise ValueError(f"Número incorrecto de capítulos ({len(datos['capitulos'])} vs {total_caps})")
                
                for idx, cap in enumerate(datos['capitulos'], 1):
                    if cap.get('num') != idx:
                        raise ValueError(f"Numeración incorrecta en capítulo {idx}")
                    
                    campos_requeridos = ['titulo', 'objetivo', 'personajes', 'ubicacion', 'eventos', 'elementos']
                    for campo in campos_requeridos:
                        if campo not in cap:
                            raise ValueError(f"Falta campo '{campo}' en capítulo {idx}")

                self.historia.context['estado']['trama'] = datos
                self.historia.context['estado']['total_caps'] = total_caps
                print("✅ Estructura de trama generada exitosamente")
                return

            except Exception as e:
                intentos += 1
                print(f"❌ Intento {intentos}/{max_intentos} fallido: {str(e)}")
                if intentos < max_intentos:
                    self.ajustar_api_parameters(intentos)
                time.sleep(2)
        
        print(f"\n⚠️ No se pudo generar una trama válida después de {max_intentos} intentos")
        print("1. Reintentar generación")
        print("2. Generar estructura básica manualmente")
        print("3. Salir del programa")
        
        opcion = input("Seleccione una opción: ").strip()
        if opcion == '1':
            self.generar_trama()
        elif opcion == '2':
            self.generar_trama_emergencia(total_caps)
        else:
            raise SystemExit("🚪 Saliendo del programa...")

    def generar_trama_emergencia(self, total_caps: int):
        print("\n🆘 Generando estructura básica de emergencia...")
        estructura = {
            "capitulos": [
                {
                    "num": i+1,
                    "titulo": f"Capítulo {i+1}",
                    "objetivo": "Desarrollo de la trama principal",
                    "personajes": list(self.historia.context['estado']['personajes'].keys())[:2],
                    "ubicacion": "Ubicación principal",
                    "eventos": ["Evento clave 1", "Evento clave 2"],
                    "elementos": self.historia.context['mundo']['elementos'][:2]
                } for i in range(total_caps)
            ]
        }
        self.historia.context['estado']['trama'] = estructura
        self.historia.context['estado']['total_caps'] = total_caps
        print("⚠️ Estructura básica generada. Deberás editar manualmente los detalles.")

    def ajustar_api_parameters(self, intento: int):
        temp = min(0.3 + (intento * 0.15), 0.8)
        max_tokens = 2000 + (intento * 500)
        print(f"⚙️  Ajustando parámetros (Temp: {temp:.1f}, Tokens: {max_tokens})")
        self.api.retry_delay = min(self.api.retry_delay * 1.5, 30)

    def generar_contenido(self):
        print("\n" + "═"*80 + "\n⌨️ Generando contenido narrativo\n" + "═"*80)
        
        trama = self.historia.context['estado']['trama']
        for cap in trama['capitulos'][self.historia.context['estado']['cap_actual']:]:
            self.historia.context['estado']['cap_actual'] = cap['num']
            print(f"\n📖 Capítulo {cap['num']}/{self.historia.context['estado']['total_caps']}")
            
            contexto = self.generar_contexto(cap['num'])
            prompt = self.construir_prompt(cap)
            mensaje_sistema = self.construir_mensaje_sistema()
            
            try:
                contenido = self.api.query(prompt, 
                                         system_message=mensaje_sistema,
                                         context=contexto,
                                         max_tokens=3800)
                contenido = self.formatear_contenido(contenido)
                cap['contenido'] = contenido
                self.actualizar_contexto(cap)
                
                if self.config['AUTO_GUARDADO']:
                    self.guardar_estado()
            except Exception as e:
                print(f"❌ Error en capítulo {cap['num']}: {str(e)}")
                self.guardar_estado(emergencia=True)
                raise

        self.generar_documentos()

    def generar_contexto(self, cap_actual: int) -> str:
        contexto = []
        inicio = max(0, cap_actual - self.config['PROFUNDIDAD_CONTEXTO'])
        
        for cap in self.historia.context['estado']['trama']['capitulos'][inicio:cap_actual]:
            contexto.append(f"Capítulo {cap['num']}: {cap['titulo']}")
            contexto.append(f"Eventos clave: {', '.join(cap['eventos'])}")
            contexto.append(f"Personajes presentes: {', '.join(cap['personajes'])}")
            contexto.append(f"Ubicación principal: {cap['ubicacion']}")
        
        return "\n".join(contexto[-6:])  # Últimos 3 capítulos

    def construir_prompt(self, cap: Dict) -> str:
        mundo = self.historia.context['mundo']
        return f"""Escribe el capítulo {cap['num']}: {cap['titulo']}
            
Contexto narrativo:
- Género: {self.historia.context['meta']['genero']}
- Elementos clave: {', '.join(mundo['elementos'])}
- Sistema: {mundo['sistema']}
- Tecnología: {mundo['tecnologia']}

Instrucciones específicas:
• Objetivo del capítulo: {cap['objetivo']}
• Personajes principales: {', '.join(cap['personajes'])}
• Ubicación principal: {cap['ubicacion']}
• Elementos a incluir: {', '.join(cap['elementos'])}
• Tema principal: {self.historia.context['meta']['tema']}
• Longitud objetivo: {self.config['MIN_PALABRAS']} palabras
• Nivel descriptivo: {self.historia.context['estado']['estilo']['descripcion']}/5"""

    def construir_mensaje_sistema(self) -> str:
        estilo = self.historia.context['estado']['estilo']
        return f"""Eres un escritor profesional de {self.historia.context['meta']['genero']}.
Reglas estilísticas:
1. Mantener coherencia con el mundo establecido
2. Usar el sistema {self.historia.context['mundo']['sistema']}
3. Formato de diálogos: {estilo['dialogos']}
4. Ritmo narrativo: {estilo['ritmo']}
5. Temas secundarios: {', '.join(self.historia.context['estado'].get('temas', []))}
6. Rating: {self.historia.context['estado']['rating']}"""

    def formatear_contenido(self, contenido: str) -> str:
        contenido = regex.sub(r'(Capítulo \d+: )#{1,3}', r'\1', contenido)
        contenido = regex.sub(r'#{2,}', '', contenido)
        
        formato_dialogos = self.historia.context['estado']['estilo']['dialogos']
        if formato_dialogos == 'guiones':
            contenido = regex.sub(r'"([^"]+)"', r'— \1', contenido)
        elif formato_dialogos == 'teatral':
            contenido = regex.sub(r'^(.*?):\s*(.*)$', r'\1\n\t\2', contenido, flags=regex.M)
        
        return contenido.strip()

    def actualizar_contexto(self, cap: Dict):
        prompt_analisis = f"""Analiza el siguiente capítulo y extrae en formato JSON:
{{
    "personajes": {{
        "nombre": {{
            "estado": str,
            "desarrollo": str
        }}
    }},
    "lugares": {{
        "nombre": {{
            "estado": str,
            "descubrimiento": str
        }}
    }},
    "eventos": [str],
    "elementos": [str]
}}

Contenido del capítulo:\n{cap['contenido']}"""
        
        try:
            analisis = self.api.query(prompt_analisis, max_tokens=1000)
            datos = self.api.safe_json_extract(analisis)
            
            if datos:
                conflictos = self.historia.actualizar_estado(datos, cap['num'])
                if conflictos:
                    print(f"⚠️ Se detectaron {len(conflictos)} conflictos de continuidad:")
                    for c in conflictos[:3]:
                        print(f" - {c}")
                    self.resolver_conflictos(conflictos)
        except Exception as e:
            print(f"⚠️ Error actualizando contexto: {str(e)}")

    def resolver_conflictos(self, conflictos: List[str]):
        print("\n🔧 Resolución de conflictos:")
        for i, conflicto in enumerate(conflictos, 1):
            print(f"{i}. {conflicto}")
        
        opc = input("\n¿Desea corregir automáticamente los conflictos? [s/n]: ").lower()
        if opc == 's':
            self.corregir_automaticamente(conflictos)
        else:
            print("⚠️ Los conflictos quedarán sin resolver. Pueden afectar la coherencia narrativa.")

    def corregir_automaticamente(self, conflictos: List[str]):
        prompt = f"""Realiza correcciones automáticas para resolver estos conflictos:
{chr(10).join(conflictos)}

Contexto actual:
{json.dumps(self.historia.context['estado'], indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)}

Genera un JSON con:
{{
    "correcciones": [
        {{
            "elemento": str,
            "campo": str,
            "valor_anterior": str,
            "valor_nuevo": str,
            "razon": str
        }}
    ]
}}"""
        
        try:
            correcciones = self.api.query(prompt, max_tokens=1000)
            datos = self.api.safe_json_extract(correcciones)
            
            if datos and 'correcciones' in datos:
                for correccion in datos['correcciones']:
                    elemento = correccion['elemento']
                    campo = correccion['campo']
                    
                    if elemento in self.historia.context['estado']['personajes']:
                        self.historia.context['estado']['personajes'][elemento][campo] = correccion['valor_nuevo']
                        print(f"✅ Corregido {elemento}.{campo}: {correccion['valor_anterior']} → {correccion['valor_nuevo']}")
                    elif elemento in self.historia.context['estado']['lugares']:
                        self.historia.context['estado']['lugares'][elemento]['actual'][campo] = correccion['valor_nuevo']
                        print(f"✅ Corregido {elemento}.{campo}: {correccion['valor_anterior']} → {correccion['valor_nuevo']}")
        except Exception as e:
            print(f"⚠️ Error aplicando correcciones: {str(e)}")

    def generar_documentos(self):
        print("\n📄 Generando documentos finales...")
        self.generar_word()
        self.guardar_textos()
        print("\n🎉 ¡Novela completada con éxito!")

    def generar_word(self):
        nombre = DocumentGenerator.generar_word(self.historia.context)
        print(f"📄 Documento Word generado: {nombre}")

    def guardar_textos(self):
        base = self.nombre_seguro(self.historia.context['meta']['titulo'])
        
        with open(f"{base}.txt", 'w', encoding='utf-8') as f:
            for cap in self.historia.context['estado']['trama']['capitulos']:
                f.write(f"CAPÍTULO {cap['num']}: {cap['titulo']}\n\n")
                f.write(cap['contenido'] + "\n\n")
        
        with open(f"{base}.json", 'w', encoding='utf-8') as f:
            json.dump(self.historia.context, f, ensure_ascii=False, indent=2, cls=EnhancedJSONEncoder)
        
        print(f"📚 Archivos generados: {base}.txt, {base}.json")

    def continuar_generacion(self):
        cap_actual = self.historia.context['estado']['cap_actual']
        print(f"\n⏩ Reanudando desde el capítulo {cap_actual + 1}")
        
        trama = self.historia.context['estado']['trama']
        trama['capitulos'] = trama['capitulos'][:cap_actual]
        self.generar_contenido()

    def ejecutar(self):
        try:
            if os.path.exists(self.archivo_backup):
                print("\n⚠️ Se detectó un backup de emergencia:")
                if input("¿Desea cargarlo y continuar? [s/n]: ").lower() == 's':
                    if self.cargar_backup(self.archivo_backup):
                        self.continuar_generacion()
                        return
            
            self.configurar_meta()
            modo = self.seleccionar_modo()
            
            if modo == '1':
                self.modo_auto()
            else:
                self.modo_manual()
            
        except Exception as e:
            print(f"\n❌ Error crítico: {str(e)}")
            self.guardar_estado(emergencia=True)
            raise

if __name__ == "__main__":
    generador = ProfessionalNovelGenerator()
    generador.ejecutar()
