from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import asyncio

class DatabaseDriver(ABC):
    """Classe base abstrata para drivers de banco de dados"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.connection_string: Optional[str] = None
        self.is_connected: bool = False
    
    @abstractmethod
    def build_connection_string(self, config: Dict[str, Any]) -> str:
        """Constrói a string de conexão específica do banco"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida a configuração do banco"""
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Retorna os campos obrigatórios para conexão"""
        pass

    def connect(self, config: Dict[str, Any]) -> bool:
        """Estabelece conexão com o banco"""
        try:
            if not self.validate_config(config):
                raise ValueError("Configuracao inválida")
            
            self.connection_string = self.build_connection_string(config)
            
            # Cria engine com configurações específicas para cada tipo de banco
            engine_args = {}
            if "sqlite" in self.connection_string:
                # Para SQLite, especifica codificação UTF-8 e outras configurações
                engine_args = {
                    "connect_args": {
                        "check_same_thread": False,
                        "isolation_level": None
                    },
                    "echo": False,
                    "pool_pre_ping": True
                }
            elif "postgresql" in self.connection_string:
                # Para PostgreSQL, configurações específicas de encoding
                engine_args = {
                    "connect_args": {
                        "client_encoding": "utf8",
                        "application_name": "db-ia-backend"
                    },
                    "echo": False,
                    "pool_pre_ping": True,
                    "pool_recycle": 300
                }
            else:
                # Para outros bancos
                engine_args = {
                    "echo": False,
                    "pool_pre_ping": True
                }
            
            self.engine = create_engine(self.connection_string, **engine_args)
            
            # Testa a conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.is_connected = False
            raise Exception(f"Erro ao conectar: {str(e)}")
    
    def disconnect(self):
        """Fecha a conexão com o banco"""
        if self.engine:
            self.engine.dispose()
            self.is_connected = False
    
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executa uma query e retorna os resultados"""
        if not self.is_connected or not self.engine:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Verifica se a query retorna linhas
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    if not rows:
                        return []
                    
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return [{"rows_affected": result.rowcount}]
                    
        except Exception as e:
            raise Exception(f"Erro ao executar query: {str(e)}")
    
    def get_tables(self) -> List[str]:
        """Retorna lista de tabelas do banco"""
        if not self.is_connected:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(self._get_tables_query()))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            raise Exception(f"Erro ao listar tabelas: {str(e)}")
    
    @abstractmethod
    def _get_tables_query(self) -> str:
        """Query específica para listar tabelas do banco"""
        pass
