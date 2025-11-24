from typing import Dict, List, Any
from .base import DatabaseDriver
import re
import urllib.parse

class PostgreSQLDriver(DatabaseDriver):
    """Driver para banco de dados PostgreSQL"""
    
    def get_required_fields(self) -> List[str]:
        return ["host", "port", "database", "username", "password"]
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do PostgreSQL"""
        required_fields = self.get_required_fields()
        
        # Verifica se todos os campos obrigatórios estão presentes
        for field in required_fields:
            if field not in config or not config[field]:
                return False
        
        # Validações específicas
        try:
            port = int(config["port"])
            if port < 1 or port > 65535:
                return False
        except (ValueError, TypeError):
            return False

        # Valida formato do host (básico)
        host = config["host"]
        if not re.match(r'^[a-zA-Z0-9.-]+$', host):
            return False
        
        return True
    
    def build_connection_string(self, config: Dict[str, Any]) -> str:
        """Constrói string de conexão PostgreSQL"""
        host = config["host"]
        port = config["port"]
        database = config["database"]
        username = config["username"]
        password = config["password"]
        
        # Escapa caracteres especiais na senha para evitar problemas de encoding
        password_escaped = urllib.parse.quote_plus(str(password))
        username_escaped = urllib.parse.quote_plus(str(username))
        
        # Adiciona parâmetros de codificação UTF-8 para evitar problemas de encoding
        return f"postgresql://{username_escaped}:{password_escaped}@{host}:{port}/{database}?client_encoding=utf8"
    
    def _get_tables_query(self) -> str:
        """Query para listar tabelas no PostgreSQL"""
        return """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Retorna informações sobre colunas da tabela"""
        if not self.is_connected:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """), {"table_name": table_name})
                
                columns = []
                for row in result.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == 'YES',
                        "default": row[3],
                        "max_length": row[4]
                    })
                return columns
        except Exception as e:
            raise Exception(f"Erro ao obter informações da tabela: {str(e)}")
    
    def get_schemas(self) -> List[str]:
        """Retorna lista de schemas disponíveis"""
        if not self.is_connected:
            raise Exception("Não conectado ao banco de dados")
        
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            raise Exception(f"Erro ao listar schemas: {str(e)}")
    
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
                        id SERIAL PRIMARY KEY,
                        produto VARCHAR(255) NOT NULL,
                        quantidade INTEGER NOT NULL,
                        preco DECIMAL(10,2) NOT NULL,
                        data_venda DATE NOT NULL,
                        vendedor VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Verifica se já existem dados
                result = conn.execute(text("SELECT COUNT(*) FROM vendas"))
                count = result.scalar()
                
                if count == 0:
                    # Insere dados de exemplo
                    conn.execute(text("""
                        INSERT INTO vendas (produto, quantidade, preco, data_venda, vendedor)
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
