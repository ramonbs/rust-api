from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
# Imports do seu sistema
from db.manager import db_manager
from llamacpp_assistant import ai_sql_llamacpp, get_llamacpp_status, llama_assistant
from pydantic import BaseModel, Field
import os
import sys
import logging

# Adiciona o diretório atual ao Python path se necessário
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Agora imports absolutos funcionarão
try:
    from db.manager import db_manager
except ImportError:
    # Fallback se a estrutura for diferente
    try:
        import db.manager as db_module
        db_manager = db_module.db_manager
    except ImportError:
        # Último fallback - assumindo que está no mesmo diretório
        from manager import db_manager

# Import do assistente LlamaCpp
try:
    from llamacpp_assistant import ai_sql_llamacpp, get_llamacpp_status, llama_assistant
except ImportError:
    # Se não existir, cria um fallback
    print("⚠️  LlamaCpp Assistant não encontrado. Funcionalidade de IA desabilitada.")
    
    def ai_sql_llamacpp(*args, **kwargs):
        return {
            "success": False,
            "error": "LlamaCpp Assistant não está disponível",
            "sql": "",
            "result": "",
            "ai_response": "Instale o llama-cpp-python e configure o assistente"
        }
    
    def get_llamacpp_status():
        return {
            "available": False,
            "model_loaded": False,
            "model_info": None,
            "db_connected": False
        }
    
    llama_assistant = None

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="DB-IA API",
    description="API para consultas em banco de dados usando IA",
    version="1.0.0"
)

# Variáveis globais para compatibilidade
AI_AVAILABLE = True
LLAMACPP_AVAILABLE = llama_assistant is not None

# Adicionar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios exatos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class LlamaCppQueryRequest(BaseModel):
    question: str
    model_path: Optional[str] = None

class DatabaseConfig(BaseModel):
    driver_type: str
    config: Dict[str, Any]

class QueryExecuteRequest(BaseModel):
    query: str

# Modelos Pydantic
class QueryRequest(BaseModel):
    question: str = Field(..., description="Pergunta em linguagem natural")
    custom_prompt: Optional[str] = Field(None, description="Prompt personalizado")

class ModelLoadRequest(BaseModel):
    model_path: str = Field(..., description="Caminho para o modelo GGUF")
    n_ctx: Optional[int] = Field(4096, description="Tamanho do contexto")
    n_threads: Optional[int] = Field(None, description="Número de threads (auto se None)")
    n_gpu_layers: Optional[int] = Field(0, description="Camadas na GPU")
    temperature: Optional[float] = Field(0.1, description="Temperatura para geração")

@app.get("/ai/status")
def get_ai_status():
    """Retorna status detalhado dos backends de IA"""
    try:
        llamacpp_status = get_llamacpp_status()
        
        status = {
            "ai_available": True,
            "backends": {
                "llamacpp": {
                    "available": True,
                    "model_loaded": llamacpp_status["model_loaded"],
                    "model_path": llamacpp_status["model_info"]["model_path"],
                    "db_connected": llamacpp_status["db_connected"],
                    "config": llamacpp_status["model_info"]["config"]
                }
            },
            "database": db_manager.get_connection_status(),
            "message": "Sistema operacional" if llamacpp_status["model_loaded"] else "Carregue um modelo para usar IA"
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/ai/load-model")
def load_model(request: ModelLoadRequest):
    """Carrega um modelo llama.cpp"""
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(request.model_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Modelo não encontrado: {request.model_path}"
            )
        
        # Carrega o modelo com configurações
        config = {
            "n_ctx": request.n_ctx,
            "n_threads": request.n_threads,
            "n_gpu_layers": request.n_gpu_layers,
            "temperature": request.temperature
        }
        
        llama_assistant.load_model(request.model_path, **config)
        
        return {
            "success": True,
            "message": f"Modelo carregado com sucesso: {request.model_path}",
            "model_info": llama_assistant.get_model_info()
        }
        
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao carregar modelo: {str(e)}"
        )

@app.delete("/ai/unload-model")
def unload_model():
    """Descarrega o modelo atual da memória"""
    try:
        llama_assistant.unload_model()
        return {
            "success": True,
            "message": "Modelo descarregado da memória"
        }
    except Exception as e:
        logger.error(f"Erro ao descarregar modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drivers")
def get_available_drivers():
    """Retorna drivers de banco disponíveis"""
    return db_manager.get_available_drivers()

@app.post("/database/connect")
def connect_database(config: DatabaseConfig):
    """Conecta a um banco de dados"""
    result = db_manager.connect(config.driver_type, config.config)
    return result

@app.post("/database/disconnect")
def disconnect_database():
    """Desconecta do banco atual"""
    result = db_manager.disconnect()
    return result

@app.get("/database/status")
def get_database_status():
    """Retorna status da conexão atual"""
    return db_manager.get_connection_status()

@app.post("/database/query")
def execute_query(request: QueryExecuteRequest):
    """Executa uma query SQL no banco conectado"""
    result = db_manager.execute_query(request.query)
    return result

@app.get("/database/tables/{table_name}/info")
def get_table_info(table_name: str):
    """Retorna informações sobre uma tabela"""
    result = db_manager.get_table_info(table_name)
    return result

@app.post("/database/sample-data")
def create_sample_data():
    """Cria dados de exemplo no banco conectado"""
    result = db_manager.create_sample_data()
    return result

@app.post("/ai/process")
def process_query_with_ai(data: QueryRequest):

    try:
        # Validações iniciais
        if not data.question.strip():
            raise HTTPException(status_code=400, detail="Pergunta não pode estar vazia")
        
        # Verifica status do sistema
        status = db_manager.get_connection_status()
        print(status)
        if not status["connected"]:
            return {
                "success": False,
                "error": "Nenhum banco de dados conectado",
                "sql": "",
                "result": "",
                "ai_response": "Conecte-se a um banco de dados primeiro.",
                "tables_available": [],
                "suggestions": ["Conecte-se a um banco PostgreSQL, MySQL ou SQLite"]
            }

        # Processa com llama.cpp
        ai_result = ai_sql_llamacpp(
            data.question, 
            custom_prompt=data.custom_prompt
        )

        print(ai_result)

        # Adiciona informações extras
        ai_result["tables_available"] = status["tables"]
        ai_result["db_info"] = {
            "driver": status["driver_type"],
            "tables_count": len(status["tables"])
        }
        
        # Adiciona sugestões em caso de erro
        if not ai_result["success"] and ai_result.get("error"):
            ai_result["suggestions"] = _get_error_suggestions(ai_result["error"])
        
        return ai_result
        
    except HTTPException:
        print("Erro HTTP capturado")
        raise HTTPException(
            status_code=400,
            detail="Erro ao processar a pergunta"
        )
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        print("Erro excepcional capturado")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Erro interno: {str(e)}",
                "suggestions": ["Verifique se o modelo está carregado", "Verifique a conexão com o banco"]
            }
        )
    finally:
        print("Finalizando processamento da pergunta")

@app.get("/ai/models")
def list_available_models():
    """Lista modelos disponíveis no diretório models/"""
    try:
        models_dir = "models"
        available_models = []
        
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith(('.gguf', '.bin')):
                    file_path = os.path.join(models_dir, file)
                    file_size = os.path.getsize(file_path)
                    available_models.append({
                        "name": file,
                        "path": file_path,
                        "size_mb": round(file_size / (1024 * 1024), 1),
                        "is_loaded": file_path == llama_assistant.model_path
                    })
        
        return {
            "models_directory": models_dir,
            "available_models": available_models,
            "current_model": llama_assistant.model_path,
            "total_models": len(available_models)
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/test-query")
def test_query(data: QueryRequest):
    """Testa uma query sem executar no banco (apenas gera SQL)"""
    try:
        if not llama_assistant.is_loaded:
            raise HTTPException(
                status_code=400, 
                detail="Nenhum modelo carregado. Use /ai/load-model primeiro."
            )
        
        # Simula execução apenas gerando SQL
        old_execute = db_manager.execute_query
        
        def mock_execute(query):
            return {
                "success": True,
                "results": ["[Simulado - Query não executada]"],
                "row_count": 0,
                "sql": query
            }
        
        # Temporariamente substitui a função
        db_manager.execute_query = mock_execute
        
        try:
            result = ai_sql_llamacpp(data.question, data.model_path)
            result["test_mode"] = True
            result["note"] = "Query gerada mas não executada (modo teste)"
            return result
        finally:
            # Restaura função original
            db_manager.execute_query = old_execute
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_error_suggestions(error_message: str) -> list:
    """Gera sugestões baseadas no tipo de erro"""
    suggestions = []
    error_lower = error_message.lower()
    
    if "modelo" in error_lower or "model" in error_lower:
        suggestions.extend([
            "Carregue um modelo usando /ai/load-model",
            "Verifique se o arquivo do modelo existe",
            "Liste modelos disponíveis em /ai/models"
        ])
    
    if "banco" in error_lower or "database" in error_lower:
        suggestions.extend([
            "Conecte-se a um banco de dados primeiro",
            "Verifique as configurações de conexão",
            "Confirme se as tabelas existem"
        ])
    
    if "sql" in error_lower or "syntax" in error_lower:
        suggestions.extend([
            "Tente reformular a pergunta",
            "Seja mais específico sobre quais dados deseja",
            "Use o modo teste (/ai/test-query) para verificar o SQL gerado"
        ])
    
    if not suggestions:
        suggestions = [
            "Verifique se o modelo está carregado",
            "Confirme a conexão com o banco de dados",
            "Tente uma pergunta mais simples"
        ]
    
    return suggestions

# Middleware para logging de requests (opcional)
@app.middleware("http")
async def log_requests(request, call_next):
    """Log de requests para debug"""
    if request.url.path.startswith("/ai/"):
        logger.info(f"AI Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    return response