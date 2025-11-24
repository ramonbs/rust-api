# llamacpp_assistant.py
from typing import Dict, Any, Optional
import os
import logging
import sys
from llama_cpp import Llama

# Adiciona o diretório atual ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import absoluto
from db.manager import db_manager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlamaCppAssistant:
    def __init__(self, model_path: str = './models/codellama-7b-instruct.Q4_K_M.gguf'):
        """
        Inicializa o LlamaCpp Assistant
        
        Args:
            model_path: Caminho para o modelo GGUF (ex: "models/llama-2-7b-chat.Q4_K_M.gguf")
        """
        self.llm = None
        self.model_path = model_path
        self.is_loaded = False
        self.model_config = {
            "n_ctx": 4096,  # Aumentado para contexto maior
            "n_threads": 8,  # Auto-detect threads
            "n_gpu_layers": 100,  # Use GPU se disponível
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 512,
            "verbose": False
        }
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, model_path: str, **kwargs):
        """
        Carrega o modelo llama.cpp com configurações otimizadas
        
        Args:
            model_path: Caminho para o modelo
            **kwargs: Configurações adicionais do modelo
        """

        default_models = [
            "codellama-7b-instruct.Q4_K_M.gguf",
            "codellama-7b-instruct-q4_k_m.gguf", 
            "llama-3.2-3b-instruct-q4_k_m.gguf",
            "llama-3.2-1b-instruct-q4_k_m.gguf"
        ]

        try:
            # Atualiza configurações se fornecidas
            config = self.model_config.copy()
            config.update(kwargs)
            
            # Auto-detecta threads se não especificado
            if config["n_threads"] is None:
                config["n_threads"] = min(8, os.cpu_count() or 4)
            
            self.model_path = model_path
            self.is_loaded = True
            logger.info(f"✅ Modelo carregado: {model_path}")
            logger.info(f"Configurações: ctx={config['n_ctx']}, threads={config['n_threads']}")

            self.llm = Llama(
                model_path=model_path,
                n_ctx=config["n_ctx"],
                n_threads=config["n_threads"],
                n_gpu_layers=config["n_gpu_layers"],
                verbose=config["verbose"]
            )

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            self.is_loaded = False
            raise
    
    def get_db_context(self) -> str:
        """Obtém o contexto do banco de dados conectado com tratamento de encoding"""
        try:
            status = db_manager.get_connection_status()
            if not status["connected"]:
                return "Nenhum banco de dados conectado."
            
            # Garante encoding UTF-8 para o contexto
            driver_type = str(status.get('driver_type', 'unknown'))

            # TODO: Melhorar o contexto para que ela entenda todo o schema de tabelas e faça relação do que o usuário pediu e tentar encontrar a info nas tabelas corretas, e não fazer pesquisas em tabelas que não exista no banco de dados atualmente.
            
            context = f"""Você é um assistente especializado em SQL para {driver_type}.
Gere queries SQL válidas e precisas baseadas nas perguntas do usuário.

Leia atentamente as informações do banco de dados e utilize-as para formular suas respostas, faça pesquisas apenas em tabelas existentes no schema.

IMPORTANTE: Responda APENAS com a query SQL, sem explicações adicionais.

Banco: {driver_type}
Tabelas disponíveis:
"""
            
            tables = status.get("tables", [])
            if not tables:
                context += "- Nenhuma tabela encontrada\n"
            else:
                for table in tables[:10]:  # Limita a 10 tabelas para não sobrecarregar o contexto
                    # Trata encoding do nome da tabela
                    safe_table_name = self._safe_string_encode(str(table))
                    context += f"- {safe_table_name}\n"
                    
                    try:
                        schema_result = db_manager.get_table_info(table)
                        if schema_result.get("success") and schema_result.get("table_info"):
                            context += f"  Colunas:\n"
                            for col_info in schema_result["table_info"][:8]:  # Limita colunas
                                col_name = self._safe_string_encode(str(col_info.get('name', 'unknown')))
                                col_type = self._safe_string_encode(str(col_info.get('type', 'unknown')))
                                context += f"    {col_name} ({col_type})\n"
                    except Exception as e:
                        logger.warning(f"Erro ao obter esquema da tabela {table}: {e}")
            
            context += self._get_sql_rules_context(driver_type)
            return context
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto do DB: {e}")
            return "Erro ao obter informações do banco de dados."
    
    def _safe_string_encode(self, text: str) -> str:
        """Garante que a string está em UTF-8 válido"""
        try:
            if isinstance(text, bytes):
                # Tenta decodificar como UTF-8
                try:
                    return text.decode('utf-8')
                except UnicodeDecodeError:
                    # Fallback para latin-1
                    return text.decode('latin-1', errors='replace')
            
            # Se já é string, garante que é UTF-8 válido
            return str(text).encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            return str(text)
    
    def _get_sql_rules_context(self, driver_type: str) -> str:
        """Retorna regras específicas do SQL baseadas no tipo de banco"""
        base_rules = """
Regras gerais:
1. Responda APENAS com SQL válido, sem comentários
2. Use LIMIT para evitar resultados grandes (máx 50 registros)
3. Para buscas use LIKE com wildcards: WHERE campo LIKE '%valor%'
4. Para contagens use COUNT(*)
5. Para somas use SUM(campo)
6. Sempre termine com ponto e vírgula (;)
"""
        
        specific_rules = {
            'postgresql': """
Regras PostgreSQL específicas:
- Use aspas duplas para nomes com espaços: "Nome Coluna"
- Para data/hora use DATE, TIMESTAMP
- Para texto use VARCHAR ou TEXT
- Funções: LOWER(), UPPER(), SUBSTRING()
""",
            'mysql': """
Regras MySQL específicas:
- Use backticks para nomes especiais: `nome_coluna`
- Para data use DATE, DATETIME
- Para texto use VARCHAR ou TEXT
- Funções: LOWER(), UPPER(), SUBSTR()
""",
            'sqlite': """
Regras SQLite específicas:
- Sintaxe mais simples
- Para data use DATE() ou datetime()
- Suporte limitado a tipos
- Funções: lower(), upper(), substr()
"""
        }
        
        driver_lower = driver_type.lower()
        specific = specific_rules.get(driver_lower, "")
        
        return base_rules + specific + """
Exemplos:
- "todos os produtos": SELECT * FROM produtos LIMIT 50;
- "total vendas": SELECT SUM(valor) FROM vendas;
- "produtos com 'notebook'": SELECT * FROM produtos WHERE nome LIKE '%notebook%' LIMIT 20;
"""

    def _clean_sql_response(self, response: str) -> str:
        """Limpa e valida a resposta SQL gerada"""
        try:
            # Remove prefixos e sufixos comuns
            cleaned = response.strip()
            
            # Remove markdown
            if '```sql' in cleaned:
                cleaned = re.sub(r'```sql\s*', '', cleaned)
            if '```' in cleaned:
                cleaned = re.sub(r'```\s*', '', cleaned)
            
            # Remove explicações após a query
            lines = cleaned.split('\n')
            sql_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Para no primeiro comentário ou explicação
                if line.startswith('--') or line.startswith('#'):
                    break
                    
                # Para em linhas que parecem explicação
                if any(word in line.lower() for word in ['esta query', 'this query', 'explicação', 'explanation']):
                    break
                    
                sql_lines.append(line)
            
            cleaned = ' '.join(sql_lines).strip()
            
            # Garante ponto e vírgula
            if cleaned and not cleaned.endswith(';'):
                cleaned += ';'
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Erro ao limpar resposta SQL: {e}")
            return response.strip()
    
    def _is_valid_sql(self, query: str) -> bool:
        """Verifica se o texto parece uma query SQL válida"""
        if not query or len(query.strip()) < 5:
            return False
        
        query_upper = query.upper().strip()
        
        # Verifica se começa com palavra-chave SQL
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']
        starts_with_sql = any(query_upper.startswith(keyword) for keyword in sql_keywords)
        
        # Verifica se contém estrutura SQL básica
        has_sql_structure = any(keyword in query_upper for keyword in ['FROM', 'WHERE', 'SET', 'VALUES'])
        
        return starts_with_sql and (has_sql_structure or query_upper.startswith('SELECT'))

    def generate_sql(self, user_question: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera SQL usando llama.cpp baseado na pergunta do usuário
        
        Args:
            user_question: Pergunta do usuário
            custom_prompt: Prompt personalizado (opcional)
        """
        try:
            # Verifica se o modelo está carregado
            if not self.is_loaded or not self.llm:
                return {
                    "success": False,
                    "error": "Modelo llama.cpp não carregado. Use load_model() primeiro.",
                    "sql": "",
                    "result": "",
                    "ai_response": "",
                    "model_info": {"loaded": False, "path": self.model_path}
                }
            print("Começou a geração do SQL")

            # Verifica conexão com DB
            status = db_manager.get_connection_status()
            if not status["connected"]:
                return {
                    "success": False,
                    "error": "Nenhum banco de dados conectado",
                    "sql": "",
                    "result": "",
                    "ai_response": "Conecte-se a um banco de dados primeiro.",
                    "model_info": {"loaded": True, "path": self.model_path}
                }
            
            # Prepara o prompt
            if custom_prompt:
                prompt = custom_prompt.format(question=user_question)
            else:
                db_context = self.get_db_context()
                prompt = f"""{db_context}

Pergunta: {user_question}

SQL:"""
            
            logger.info(f"Gerando SQL para: {user_question}")

            print("chegou aqui antes da geração do SQL 3")

            
            # Gera resposta usando llama.cpp
            response = self.llm(
                prompt,
                max_tokens=self.model_config["max_tokens"],
                temperature=self.model_config["temperature"],
                top_p=self.model_config["top_p"],
                stop=["\n\n", "```", "Pergunta:", "Question:", "--"],
                echo=False
            )
            
            ai_generated_text = response['choices'][0]['text'].strip()
            logger.info(f"Resposta bruta da IA: {ai_generated_text}")
            
            # Limpa a resposta
            sql_query = self._clean_sql_response(ai_generated_text)
            
            # Verifica se é SQL válido
            if self._is_valid_sql(sql_query):
                logger.info(f"Query SQL gerada: {sql_query}")
                
                # Executa a query
                execution_result = db_manager.execute_query(sql_query)
                
                if execution_result["success"]:
                    return {
                        "success": True,
                        "sql": sql_query,
                        "result": execution_result["results"],
                        "row_count": execution_result.get("row_count", 0),
                        "ai_response": f"Query executada com sucesso. {execution_result.get('row_count', 0)} registros retornados.",
                        "execution_time": execution_result.get("execution_time"),
                        "model_info": {"loaded": True, "path": self.model_path}
                    }
                else:
                    return {
                        "success": False,
                        "error": execution_result["error"],
                        "sql": sql_query,
                        "result": "",
                        "ai_response": f"Query gerada mas falhou na execução: {execution_result['error']}",
                        "model_info": {"loaded": True, "path": self.model_path}
                    }
            else:
                # Não é SQL válido, retorna resposta da IA como texto
                return {
                    "success": True,
                    "sql": "",
                    "result": "",
                    "ai_response": ai_generated_text,
                    "model_info": {"loaded": True, "path": self.model_path}
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar SQL: {e}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}",
                "sql": "",
                "result": "",
                "ai_response": "",
                "model_info": {"loaded": self.is_loaded, "path": self.model_path}
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo carregado"""
        return {
            "loaded": self.is_loaded,
            "model_path": self.model_path,
            "config": self.model_config if self.is_loaded else None
        }
    
    def unload_model(self):
        """Descarrega o modelo da memória"""
        if self.llm:
            del self.llm
            self.llm = None
        self.is_loaded = False
        logger.info("Modelo descarregado da memória")

# Instância global do assistente llama.cpp
llama_assistant = LlamaCppAssistant()

def ai_sql_llamacpp(user_question: str, model_path: str = None, **kwargs) -> Dict[str, Any]:
    """
    Função wrapper melhorada para usar llama.cpp
    
    Args:
        user_question: Pergunta do usuário
        model_path: Caminho do modelo (opcional)
        **kwargs: Argumentos adicionais (custom_prompt, etc.)
    """
    global llama_assistant
    
    try:
        # Se um caminho de modelo foi fornecido e é diferente do atual, recarrega
        if model_path and model_path != llama_assistant.model_path:
            if os.path.exists(model_path):
                llama_assistant.load_model(model_path)
            else:
                return {
                    "success": False,
                    "error": f"Modelo não encontrado: {model_path}",
                    "sql": "",
                    "result": "",
                    "ai_response": "",
                    "model_info": {"loaded": False, "path": model_path}
                }
        
        # Se não há modelo carregado e não foi fornecido caminho
        if not llama_assistant.is_loaded and not model_path:
            return {
                "success": False,
                "error": "Nenhum modelo carregado. Forneça model_path ou carregue um modelo primeiro.",
                "sql": "",
                "result": "",
                "ai_response": "",
                "model_info": {"loaded": False, "path": None}
            }
        
        print("chegou aqui antes da geração do SQL")

        return llama_assistant.generate_sql(user_question, **kwargs)
        
    except Exception as e:
        logger.error(f"Erro na função wrapper: {e}")
        return {
            "success": False,
            "error": f"Erro no wrapper llama.cpp: {str(e)}",
            "sql": "",
            "result": "",
            "ai_response": "",
            "model_info": llama_assistant.get_model_info()
        }

def get_llamacpp_status() -> Dict[str, Any]:
    """Retorna status detalhado do LlamaCpp Assistant"""
    return {
        "available": True,  # llama-cpp-python está instalado
        "model_loaded": llama_assistant.is_loaded,
        "model_info": llama_assistant.get_model_info(),
        "db_connected": db_manager.get_connection_status()["connected"]
    }