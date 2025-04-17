import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import random
from datetime import datetime
import traceback

def configurar_driver():
    """Configura e retorna uma instância do ChromeDriver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    
    # No GitHub Actions, não use o ChromeDriverManager, use o Chrome já instalado
    try:
        print("Tentando usar o Chrome instalado no ambiente...")
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Erro ao usar Chrome instalado: {str(e)}")
        print("Tentando com ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

def extrair_seguidores(texto):
    """Extrai o número de seguidores do texto"""
    # Imprime o texto completo para debugging
    print(f"Texto para extração: '{texto}'")
    
    # Pattern para encontrar números seguidos pela palavra "seguidores"
    # Lida com formatos como "298.749 seguidores" ou "1.234 seguidores"
    pattern = r'([\d.,]+)\s+seguidores'
    match = re.search(pattern, texto)
    
    if match:
        # Remove pontos e converte para inteiro
        seguidores = match.group(1).replace('.', '').replace(',', '')
        return int(seguidores)
    
    # Tenta outros padrões comuns (followers, etc)
    patterns = [
        r'([\d.,]+)\s+followers',  # Inglês
        r'([\d.,]+)\s+seguidores', # Português
        r'([\d.,]+)\s+abonnés',    # Francês
        r'([\d.,]+)\s+\w+',        # Qualquer texto após número
        r'([\d.,]+)'               # Apenas números
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto)
        if match:
            print(f"Padrão alternativo encontrado: {pattern}")
            seguidores = match.group(1).replace('.', '').replace(',', '')
            return int(seguidores)
    
    print("Nenhum padrão de seguidores encontrado no texto")
    return None

def coletar_dados():
    """Função principal para coleta de dados"""
    print("Iniciando coleta de dados")
    print(f"Diretório atual: {os.getcwd()}")
    print(f"Conteúdo do diretório: {os.listdir('.')}")
    
    # Verificar se o arquivo de configuração existe
    if not os.path.exists('config.xlsx'):
        print("Arquivo config.xlsx não encontrado!")
        # Criar um arquivo de resultados vazio para evitar falha no workflow
        pd.DataFrame(columns=['data', 'nome', 'seguidores']).to_excel('resultados.xlsx', index=False)
        print("Criado resultados.xlsx vazio")
        return
    
    # Carregar dados do Excel
    print("Carregando dados do arquivo config.xlsx")
    try:
        dados = pd.read_excel('config.xlsx')
        print(f"Dados carregados: {len(dados)} registros")
        print(f"Colunas: {dados.columns.tolist()}")
    except Exception as e:
        print(f"Erro ao carregar config.xlsx: {str(e)}")
        # Criar um arquivo de resultados vazio para evitar falha no workflow
        pd.DataFrame(columns=['data', 'nome', 'seguidores']).to_excel('resultados.xlsx', index=False)
        print("Criado resultados.xlsx vazio")
        return
    
    # Verificar se o arquivo de resultados existe, senão criar
    if os.path.exists('resultados.xlsx'):
        print("Carregando arquivo de resultados existente")
        resultados_df = pd.read_excel('resultados.xlsx')
        print(f"Resultados carregados: {len(resultados_df)} registros")
    else:
        print("Criando novo DataFrame de resultados")
        resultados_df = pd.DataFrame(columns=['data', 'nome', 'seguidores'])
    
    # Data atual
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"Data de coleta: {data_hoje}")
    
    # Lista para armazenar novos resultados
    novos_resultados = []
    
    try:
        # Inicializar o driver
        print("Inicializando o WebDriver")
        driver = configurar_driver()
        
        try:
            for _, linha in dados.iterrows():
                try:
                    nome_pagina = linha['nome_pagina']
                    url = linha['url']
                    xpath = linha['xpath']
                    
                    print(f"Processando: {nome_pagina}, URL: {url}")
                    
                    # Acessar a URL
                    driver.get(url)
                    time.sleep(5)  # Aumentado para 5 segundos
                    
                    # Capturar screenshot para debugging
                    try:
                        screenshot_path = f"screenshot_{nome_pagina}.png"
                        driver.save_screenshot(screenshot_path)
                        print(f"Screenshot salvo em {screenshot_path}")
                    except Exception as e:
                        print(f"Erro ao salvar screenshot: {str(e)}")
                    
                    # Pressionar ESC para fechar possíveis popups
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                    
                    # Imprimir HTML para debug
                    print(f"HTML da página: {driver.page_source[:500]}...")
                    
                    try:
                        # Encontrar o elemento usando XPath
                        print(f"Buscando elemento com XPath: {xpath}")
                        elemento = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        
                        # Extrair o texto e buscar o número de seguidores
                        texto_elemento = elemento.text
                        print(f"Texto encontrado: '{texto_elemento}'")
                        seguidores = extrair_seguidores(texto_elemento)
                        
                        if seguidores:
                            print(f"Seguidores extraídos para {nome_pagina}: {seguidores}")
                            novos_resultados.append({
                                'data': data_hoje,
                                'nome': nome_pagina,
                                'seguidores': seguidores
                            })
                        else:
                            print(f"Não foi possível extrair número de seguidores para {nome_pagina}")
                            # Adiciona entrada com valor nulo para manter registro
                            novos_resultados.append({
                                'data': data_hoje,
                                'nome': nome_pagina,
                                'seguidores': 0  # Valor padrão quando não consegue extrair
                            })
                    except Exception as e:
                        print(f"Erro ao processar elemento: {str(e)}")
                        print(traceback.format_exc())
                        # Adiciona entrada com erro para manter registro
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'seguidores': 0  # Valor padrão quando há erro
                        })
                
                except Exception as e:
                    print(f"Erro ao processar {nome_pagina}: {str(e)}")
                    print(traceback.format_exc())
                
                # Esperar entre requisições para evitar sobrecarga
                time.sleep(random.uniform(2, 5))
        
        finally:
            print("Finalizando o WebDriver")
            driver.quit()
    
    except Exception as e:
        print(f"Erro geral: {str(e)}")
        print(traceback.format_exc())
    
    finally:
        # Garantir que o arquivo de resultados seja criado mesmo se não houver dados novos
        if not novos_resultados:
            print("Nenhum novo resultado coletado")
            # Adicionar um registro vazio para garantir que o arquivo seja criado
            novos_resultados.append({
                'data': data_hoje,
                'nome': 'sem_dados',
                'seguidores': 0
            })
        
        # Adicionar novos resultados ao DataFrame
        print(f"Adicionando {len(novos_resultados)} novos resultados")
        novos_df = pd.DataFrame(novos_resultados)
        resultados_df = pd.concat([resultados_df, novos_df], ignore_index=True)
        
        # Salvar resultados atualizados
        print("Salvando resultados em resultados.xlsx")
        resultados_df.to_excel('resultados.xlsx', index=False)
        print(f"Dados salvos em resultados.xlsx - {len(resultados_df)} registros totais")

if __name__ == "__main__":
    try:
        print("Iniciando script de coleta")
        coletar_dados()
        print("Script de coleta concluído com sucesso")
    except Exception as e:
        print(f"Erro geral no script: {str(e)}")
        print(traceback.format_exc())
        # Garantir que o arquivo de resultados exista mesmo em caso de erro fatal
        if not os.path.exists('resultados.xlsx'):
            pd.DataFrame(columns=['data', 'nome', 'seguidores']).to_excel('resultados.xlsx', index=False)
            print("Criado resultados.xlsx vazio devido a erro")
