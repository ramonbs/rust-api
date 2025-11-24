import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import DatabaseConfig from './components/DatabaseConfig';
import RefreshButton from './components/RefreshButton';

interface DatabaseStatus {
  connected: boolean;
  driver_type: string | null;
  tables: string[];
}

function App() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [databaseStatus, setDatabaseStatus] = useState<DatabaseStatus>({
    connected: false,
    driver_type: null,
    tables: []
  });

  async function sendQuestion() {
    if (!databaseStatus.connected) {
      setResponse('❌ Conecte-se a um banco de dados primeiro!');
      return;
    }

    try {
      const res = await invoke<string>('send_query', { question });
      setResponse(res);
    } catch (error) {
      setResponse('❌ Erro ao conectar com backend.');
    }
  }

  const handleConnectionChange = (status: DatabaseStatus) => {
    setDatabaseStatus(status);
    if (status.connected) {
      setResponse(`✅ Conectado ao ${status.driver_type}! Tabelas disponíveis: ${status.tables.join(', ')}`);
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: 'Arial', maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', color: '#333', marginBottom: 30 }}>
        🤖 Consulta IA DB
      </h1>
      
      {/* Configuração do Banco */}
      <DatabaseConfig onConnectionChange={handleConnectionChange} />
      
      {/* Interface de Consulta */}
      <div style={{ 
        marginTop: 30, 
        padding: 20, 
        backgroundColor: '#f8f9fa', 
        borderRadius: 8,
        border: '1px solid #dee2e6'
      }}>
        <h2 style={{ marginTop: 0, color: '#495057' }}>💬 Fazer Pergunta à IA</h2>
        
        {/* Exemplos de perguntas */}
        {databaseStatus.connected && databaseStatus.tables.length > 0 && (
          <div style={{ 
            marginBottom: 15, 
            padding: 10, 
            backgroundColor: '#e7f3ff', 
            borderRadius: 4,
            fontSize: 13
          }}>
            <strong>💡 Exemplos de perguntas:</strong>
            <div style={{ marginTop: 5 }}>
              {databaseStatus.tables.includes('vendas') && (
                <>
                  • "Mostre todas as vendas" <br/>
                  • "Qual o total de vendas?" <br/>
                  • "Quem são os melhores vendedores?" <br/>
                </>
              )}
              • "Quantos registros temos na tabela {databaseStatus.tables[0]}?" <br/>
              • "Mostre o esquema das tabelas disponíveis"
            </div>
          </div>
        )}
        
        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
          <input
            type="text"
            placeholder={
              databaseStatus.connected 
                ? "Digite sua pergunta sobre os dados..." 
                : "Conecte-se a um banco primeiro"
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={!databaseStatus.connected}
            style={{ 
              flex: 1, 
              padding: '12px', 
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: databaseStatus.connected ? 'white' : '#f8f9fa'
            }}
            onKeyPress={(e) => e.key === 'Enter' && sendQuestion()}
          />
          <button 
            onClick={sendQuestion} 
            disabled={!databaseStatus.connected || !question.trim()}
            style={{ 
              padding: '12px 24px',
              backgroundColor: databaseStatus.connected && question.trim() ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: databaseStatus.connected && question.trim() ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Enviar
          </button>
        </div>

        {databaseStatus.connected && databaseStatus.tables.length === 0 && (
          <>
          <div style={{ 
            padding: 15, 
            backgroundColor: '#fff3cd', 
            border: '1px solid #ffeaa7',
            borderRadius: 4,
            marginBottom: 20,
            color: '#856404'
          }}>
            ⚠️ Nenhuma tabela encontrada no banco. Crie dados de exemplo usando o botão na configuração.
          </div>
          <RefreshButton onRefresh={() => invoke('get_database_status')} />
          </>
        )}
        
        <div style={{ 
          marginTop: 20, 
          backgroundColor: 'white',
          padding: 20,
          borderRadius: 6,
          border: '1px solid #dee2e6',
          minHeight: 120
        }}>
          <strong style={{ color: '#495057', fontSize: 16 }}>🤖 Resposta da IA:</strong>
          
          {response ? (
            <div style={{ 
              marginTop: 15,
              padding: 15,
              backgroundColor: response.includes('❌') ? '#f8d7da' : '#f8f9fa',
              borderRadius: 4,
              border: `1px solid ${response.includes('❌') ? '#f5c6cb' : '#dee2e6'}`
            }}>
              <pre style={{ 
                margin: 0, 
                fontFamily: 'Monaco, Consolas, "Lucida Console", monospace',
                fontSize: 13,
                lineHeight: 1.4,
                whiteSpace: 'pre-wrap',
                color: response.includes('❌') ? '#721c24' : '#495057'
              }}>
                {response}
              </pre>
            </div>
          ) : (
            <div style={{ 
              marginTop: 15,
              padding: 20,
              textAlign: 'center',
              color: '#6c757d',
              fontStyle: 'italic',
              backgroundColor: '#f8f9fa',
              borderRadius: 4,
              border: '1px solid #dee2e6'
            }}>
              Faça uma pergunta para ver a resposta da IA aqui...
            </div>
          )}
        </div>
      </div>

      {/* Informações sobre o status */}
      <div style={{ 
        marginTop: 20, 
        padding: 15, 
        backgroundColor: databaseStatus.connected ? '#d4edda' : '#f8d7da',
        border: `1px solid ${databaseStatus.connected ? '#c3e6cb' : '#f5c6cb'}`,
        borderRadius: 4,
        fontSize: 14
      }}>
        <strong>Status: </strong>
        {databaseStatus.connected ? (
          <span style={{ color: '#155724' }}>
            ✅ Conectado ao {databaseStatus.driver_type} ({databaseStatus.tables.length} tabelas)
          </span>
        ) : (
          <span style={{ color: '#721c24' }}>
            ❌ Não conectado - Configure um banco de dados acima
          </span>
        )}
      </div>
    </div>
  );
}

export default App;
