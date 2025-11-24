#!/usr/bin/env python3
"""
Script para baixar modelos GGUF para llama.cpp
Este script baixa modelos recomendados do Hugging Face
"""

import os
import requests
from tqdm import tqdm
import sys

def download_file(url, filename, chunk_size=1024*1024):
    """Download de arquivo com barra de progresso"""
    print(f"📥 Baixando: {filename}")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✅ Download concluído: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def main():
    """Função principal"""
    
    # Cria diretório models se não existir
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Modelos recomendados (do menor para o maior)
    models = {
        "1": {
            "name": "Llama 3.2 1B Instruct (Pequeno - 1.2GB)",
            "file": "llama-3.2-1b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
            "description": "Modelo pequeno e rápido, ideal para testes"
        },
        "2": {
            "name": "Llama 3.2 3B Instruct (Médio - 2.0GB)",
            "file": "llama-3.2-3b-instruct-q4_k_m.gguf", 
            "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "description": "Bom equilíbrio entre tamanho e qualidade"
        },
        "3": {
            "name": "CodeLlama 7B Instruct (Especializado em código - 4.1GB)",
            "file": "codellama-7b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
            "description": "Especializado em geração de código e SQL"
        },
        "4": {
            "name": "Llama 3.1 8B Instruct (Grande - 4.9GB)",
            "file": "llama-3.1-8b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "description": "Modelo grande com alta qualidade"
        }
    }
    
    print("🤖 Download de Modelos para llama.cpp")
    print("=" * 50)
    print("\nModelos disponíveis:")
    
    for key, model in models.items():
        print(f"{key}. {model['name']}")
        print(f"   📁 {model['file']}")
        print(f"   📝 {model['description']}")
        print()
    
    # Recomendação baseada na RAM
    print("💡 Recomendações:")
    print("   • 4-8GB RAM: Opção 1 (1B)")
    print("   • 8-16GB RAM: Opção 2 (3B)")  
    print("   • 16+GB RAM: Opção 3 ou 4 (7B-8B)")
    print()
    
    while True:
        try:
            choice = input("Escolha um modelo (1-4) ou 'q' para sair: ").strip().lower()
            
            if choice == 'q':
                print("👋 Saindo...")
                return
            
            if choice not in models:
                print("❌ Opção inválida!")
                continue
                
            model = models[choice]
            filepath = os.path.join(models_dir, model['file'])
            
            # Verifica se já existe
            if os.path.exists(filepath):
                overwrite = input(f"📄 Arquivo {model['file']} já existe. Sobrescrever? (s/N): ").strip().lower()
                if overwrite not in ['s', 'sim', 'y', 'yes']:
                    print("⏩ Download cancelado.")
                    continue
            
            print(f"\n🚀 Iniciando download de {model['name']}")
            
            # Faz o download
            if download_file(model['url'], filepath):
                print(f"\n✅ Modelo baixado com sucesso!")
                print(f"📍 Local: {filepath}")
                print(f"\n🔧 Para usar este modelo na aplicação:")
                print(f"   Caminho: {os.path.abspath(filepath)}")
                print(f"\n💡 Próximos passos:")
                print(f"   1. Cole o caminho acima na interface da aplicação")
                print(f"   2. Clique em 'Carregar Modelo'")
                print(f"   3. Teste fazendo uma pergunta!")
                break
            else:
                print("❌ Falha no download. Tente novamente.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Download interrompido pelo usuário.")
            return
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
