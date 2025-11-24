import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import './DatabaseConfig.css';

interface Driver {
  name: string;
  description: string;
  required_fields: string[];
  field_types: Record<string, string>;
}

interface DatabaseStatus {
  connected: boolean;
  driver_type: string | null;
  tables: string[];
}

interface DatabaseConfigProps {
  onConnectionChange: (status: DatabaseStatus) => void;
}

const DatabaseConfig: React.FC<DatabaseConfigProps> = ({ onConnectionChange }) => {
  const [drivers, setDrivers] = useState<Record<string, Driver>>({});
  const [selectedDriver, setSelectedDriver] = useState<string>('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<DatabaseStatus>({
    connected: false,
    driver_type: null,
    tables: []
  });
  const [message, setMessage] = useState<string>('');
  const [showConfig, setShowConfig] = useState(false);

  useEffect(() => {
    loadDrivers();
    checkConnectionStatus();
  }, []);

  const loadDrivers = async () => {
    try {
      const response = await invoke<Record<string, Driver>>('get_database_drivers');
      setDrivers(response);
    } catch (error) {
      console.error('Erro ao carregar drivers:', error);
      setMessage('Erro ao carregar drivers de banco de dados');
    }
  };

  const checkConnectionStatus = async () => {
    try {
      const status = await invoke<DatabaseStatus>('get_database_status');
      setConnectionStatus(status);
      onConnectionChange(status);
    } catch (error) {
      console.error('Erro ao verificar status:', error);
    }
  };

  const handleDriverChange = (driverType: string) => {
    setSelectedDriver(driverType);
    setConfig({});
    setMessage('');
    
    // Inicializa campos com valores padrão
    if (drivers[driverType]) {
      const newConfig: Record<string, any> = {};
      drivers[driverType].required_fields.forEach(field => {
        if (field === 'port' && driverType === 'postgresql') {
          newConfig[field] = 5432;
        } else if (field === 'host' && driverType === 'postgresql') {
          newConfig[field] = 'localhost';
        } else {
          newConfig[field] = '';
        }
      });
      setConfig(newConfig);
    }
  };

  const handleConfigChange = (field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleConnect = async () => {
    if (!selectedDriver) {
      setMessage('Selecione um driver de banco de dados');
      return;
    }

    setIsConnecting(true);
    setMessage('');

    try {
      const result = await invoke<{ success: boolean; message: string; tables: string[]; driver_type: string }>('connect_database', {
        driverType: selectedDriver,
        config: config
      });

      if (result.success) {
        setMessage(`✅ ${result.message}`);
        const newStatus = {
          connected: true,
          driver_type: result.driver_type,
          tables: result.tables || []
        };
        setConnectionStatus(newStatus);
        onConnectionChange(newStatus);
        setShowConfig(false);
      } else {
        setMessage(`❌ ${result.message}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await invoke('disconnect_database');
      setMessage('Desconectado com sucesso');
      const newStatus = {
        connected: false,
        driver_type: null,
        tables: []
      };
      setConnectionStatus(newStatus);
      onConnectionChange(newStatus);
    } catch (error) {
      setMessage(`❌ Erro ao desconectar: ${error}`);
    }
  };

  const createSampleData = async () => {
    try {
      const result = await invoke<{ success: boolean; message: string }>('create_sample_data');
      if (result.success) {
        setMessage(`✅ ${result.message}`);
        // Atualiza status para recarregar tabelas
        await checkConnectionStatus();
      } else {
        setMessage(`❌ Erro ao criar dados: ${result.message}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    }
  };

  const renderFieldInput = (field: string, type: string) => {
    const value = config[field] || '';
    
    switch (type) {
      case 'password':
        return (
          <input
            type="password"
            value={value}
            onChange={(e) => handleConfigChange(field, e.target.value)}
            placeholder={`Digite ${field}`}
            className="config-input"
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleConfigChange(field, parseInt(e.target.value) || '')}
            placeholder={`Digite ${field}`}
            className="config-input"
          />
        );
      case 'file':
        return (
          <div className="file-input-group">
            <input
              type="text"
              value={value}
              onChange={(e) => handleConfigChange(field, e.target.value)}
              placeholder="Caminho do arquivo (ex: ./database.db)"
              className="config-input"
            />
            <small className="help-text">
              Para SQLite, pode ser um caminho relativo ou absoluto
            </small>
          </div>
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleConfigChange(field, e.target.value)}
            placeholder={`Digite ${field}`}
            className="config-input"
          />
        );
    }
  };

  return (
    <div className="database-config">
      <div className="config-header">
        <h2>🗄️ Configuração de Banco de Dados</h2>
        
        {connectionStatus.connected ? (
          <div className="connection-status connected">
            <span className="status-indicator">●</span>
            Conectado ao {connectionStatus.driver_type}
            <button onClick={handleDisconnect} className="btn btn-danger btn-sm">
              Desconectar
            </button>
          </div>
        ) : (
          <div className="connection-status disconnected">
            <span className="status-indicator">●</span>
            Não conectado
            <button 
              onClick={() => setShowConfig(!showConfig)} 
              className="btn btn-primary btn-sm"
            >
              {showConfig ? 'Ocultar Config' : 'Configurar Banco'}
            </button>
          </div>
        )}
      </div>

      {connectionStatus.connected && (
        <div className="connected-info">
          <h3>Tabelas disponíveis ({connectionStatus.tables.length}):</h3>
          <div className="tables-list">
            {connectionStatus.tables.length > 0 ? (
              connectionStatus.tables.map(table => (
                <span key={table} className="table-tag">{table}</span>
              ))
            ) : (
              <span className="no-tables">Nenhuma tabela encontrada</span>
            )}
          </div>
          <button onClick={createSampleData} className="btn btn-secondary btn-sm">
            Criar Dados de Exemplo
          </button>
        </div>
      )}

      {showConfig && (
        <div className="config-form">
          <div className="form-group">
            <label>Tipo de Banco:</label>
            <select 
              value={selectedDriver} 
              onChange={(e) => handleDriverChange(e.target.value)}
              className="driver-select"
            >
              <option value="">Selecione um banco...</option>
              {Object.entries(drivers).map(([key, driver]) => (
                <option key={key} value={key}>
                  {driver.name} - {driver.description}
                </option>
              ))}
            </select>
          </div>

          {selectedDriver && drivers[selectedDriver] && (
            <div className="driver-config">
              <h3>Configuração - {drivers[selectedDriver].name}</h3>
              {drivers[selectedDriver].required_fields.map(field => (
                <div key={field} className="form-group">
                  <label>{field.charAt(0).toUpperCase() + field.slice(1)}:</label>
                  {renderFieldInput(field, drivers[selectedDriver].field_types[field] || 'text')}
                </div>
              ))}
              
              <div className="form-actions">
                <button 
                  onClick={handleConnect} 
                  disabled={isConnecting}
                  className="btn btn-primary"
                >
                  {isConnecting ? 'Conectando...' : 'Conectar'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default DatabaseConfig;
