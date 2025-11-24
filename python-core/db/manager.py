from typing import Dict, Any, Optional
from .drivers.base import DatabaseDriver
from .drivers.sqlite_driver import SQLiteDriver
from .drivers.postgresql_driver import PostgreSQLDriver

class DatabaseManager:
    """Gerenciador centralizado de conexões de banco de dados"""
    
    def __init__(self):
        self.current_driver: Optional[DatabaseDriver] = None
        self.current_config: Optional[Dict[str, Any]] = None
        self.drivers = {
            "sqlite": SQLiteDriver,
            "postgresql": PostgreSQLDriver
        }
    
    def get_available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre drivers disponíveis"""
        return {
            "sqlite": {
                "name": "SQLite",
                "description": "Banco de dados local em arquivo",
                "required_fields": SQLiteDriver().get_required_fields(),
                "field_types": {
                    "database_path": "file"
                }
            },
            "postgresql": {
                "name": "PostgreSQL",
                "description": "Banco de dados PostgreSQL",
                "required_fields": PostgreSQLDriver().get_required_fields(),
                "field_types": {
                    "host": "text",
                    "port": "number",
                    "database": "text",
                    "username": "text",
                    "password": "password"
                }
            }
        }
    
    def connect(self, driver_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Conecta a um banco de dados"""

        try:
            # Desconecta da conexão atual se existir
            if self.current_driver:
                self.current_driver.disconnect()
            
            # Verifica se o driver existe
            if driver_type not in self.drivers:
                raise ValueError(f"Driver '{driver_type}' não suportado")
            
            # Cria nova instância do driver
            driver_class = self.drivers[driver_type]
            self.current_driver = driver_class()


            # Tenta conectar
            success = self.current_driver.connect(config)

            if success:
                self.current_config = config.copy()
                self.current_config["driver_type"] = driver_type
                
                return {
                    "success": True,
                    "message": f"Conectado com sucesso ao {driver_type}",
                    "driver_type": driver_type,
                    "tables": self.current_driver.get_tables()
                }
            else:
                return {
                    "success": False,
                    "message": "Falha na conexão",
                    "driver_type": driver_type,
                    "tables": []
                }

        except Exception as e:
            self.current_driver = None
            self.current_config = None

            return {
                "success": False,
                "message": str(e),
                "driver_type": None,
                "tables": []
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """Desconecta do banco atual"""
        try:
            if self.current_driver:
                self.current_driver.disconnect()
                self.current_driver = None
                self.current_config = None
                
            return {
                "success": True,
                "message": "Desconectado com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Retorna status da conexão atual"""
        if self.current_driver and self.current_driver.is_connected:
            return {
                "connected": True,
                "driver_type": self.current_config.get("driver_type"),
                "tables": self.current_driver.get_tables()
            }
        else:
            return {
                "connected": False,
                "driver_type": None,
                "tables": []
            }

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Executa uma query no banco conectado"""
        try:
            if not self.current_driver or not self.current_driver.is_connected:
                raise Exception("Não há conexão ativa com banco de dados")
            
            results = self.current_driver.execute_query(query)
            
            return {
                "success": True,
                "results": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "row_count": 0
            }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Retorna informações sobre uma tabela"""
        try:
            if not self.current_driver or not self.current_driver.is_connected:
                raise Exception("Não há conexão ativa com banco de dados")
            
            if hasattr(self.current_driver, 'get_table_info'):
                info = self.current_driver.get_table_info(table_name)
                return {
                    "success": True,
                    "table_info": info
                }
            else:
                raise Exception("Driver não suporta informações de tabela")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "table_info": []
            }
    
    def create_sample_data(self) -> Dict[str, Any]:
        """Cria dados de exemplo no banco conectado"""
        try:
            if not self.current_driver or not self.current_driver.is_connected:
                raise Exception("Não há conexão ativa com banco de dados")
            
            if hasattr(self.current_driver, 'create_sample_data'):
                self.current_driver.create_sample_data()
                return {
                    "success": True,
                    "message": "Dados de exemplo criados com sucesso"
                }
            else:
                raise Exception("Driver não suporta criação de dados de exemplo")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Instância global do gerenciador
db_manager = DatabaseManager()
