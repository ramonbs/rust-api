import os
from typing import Dict, List, Any
from .base import DatabaseDriver

class SQLiteDriver(DatabaseDriver):
    """Driver para banco de dados SQLite"""
    
    def get_required_fields(self) -> List[str]:
        return ["database_path"]
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do SQLite"""
        required_fields = self.get_required_fields()
        
        # Verifica se todos os campos obrigatórios estão presentes
        for field in required_fields:
            if field not in config or not config[field]:
                return False
        
        database_path = config["database_path"]
        
        # Se o arquivo não existir, verifica se o diretório pai existe ou pode ser criado
        if not os.path.exists(database_path):
            parent_dir = os.path.dirname(database_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception:
                    return False
        
        return True
    
    def build_connection_string(self, config: Dict[str, Any]) -> str:
        """Constrói string de conexão SQLite"""
        database_path = config["database_path"]
        
        # Normaliza o caminho e converte para formato adequado
        database_path = os.path.abspath(database_path)
        
        # Para Windows, converte barras invertidas
        if os.name == 'nt':  # Windows
            database_path = database_path.replace('\\', '/')
        
        return f"sqlite:///{database_path}"
    
    def _get_tables_query(self) -> str:
        """Query para listar tabelas no SQLite"""
        return """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Retorna informações sobre colunas da tabela"""
        if not self.is_connected:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = []
                for row in result.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "primary_key": bool(row[5])
                    })
                return columns
        except Exception as e:
            raise Exception(f"Erro ao obter informações da tabela: {str(e)}")
    
    def create_sample_data(self):
        """Cria dados de exemplo para testes"""
        if not self.is_connected:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                
                # Cria tabela de exemplo
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS vendas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        produto TEXT NOT NULL,
                        quantidade INTEGER NOT NULL,
                        preco REAL NOT NULL,
                        data_venda DATE NOT NULL,
                        vendedor TEXT NOT NULL
                    )
                """))
                
                # Insere dados de exemplo
                conn.execute(text("""
                    INSERT OR IGNORE INTO vendas (produto, quantidade, preco, data_venda, vendedor)
                    VALUES 
                    ('Notebook Dell', 2, 2500.00, '2024-01-15', 'João Silva'),
                    ('Mouse Logitech', 5, 120.00, '2024-01-16', 'Maria Santos'),
                    ('Teclado Mecânico', 3, 350.00, '2024-01-17', 'Pedro Costa'),
                    ('Monitor 24"', 1, 800.00, '2024-01-18', 'Ana Oliveira'),
                    ('SSD 1TB', 4, 400.00, '2024-01-19', 'Carlos Lima')
                """))
                
                conn.commit()
                
        except Exception as e:
            raise Exception(f"Erro ao criar dados de exemplo: {str(e)}")
