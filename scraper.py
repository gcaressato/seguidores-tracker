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
import json
import yaml
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
    
    # No GitHub Actions, use o Chrome já instalado
    try:
        print("Usando o Chrome instalado no ambiente...")
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

def carregar_configuracao():
    """Carrega a configuração do arquivo config.json, config.yaml ou config.xlsx"""
    # Tentar carregar de config.json primeiro
    if os.path.exists('config.json'):
        print("Carregando configuração de config.json")
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return pd.DataFrame(config)
    
    # Tentar carregar de config.yaml em seguida
    elif os.path.exists('config.yaml') or os.path.exists('config.yml'):
        yaml_file = 'config.yaml' if os.path.exists('config.yaml') else 'config.yml'
        print(f"Carregando configuração de {yaml_file}")
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return pd.DataFrame(config)
    
    # Finalmente, tentar carregar de config.xlsx
    elif os.path.exists('config.xlsx'):
        print("Carregando configuração de config.xlsx")
        return pd.read_excel('config.xlsx')
    
    else:
        print("Nenhum arquivo de configuração encontrado (config.json, config.yaml, config.xlsx)")
        # Criar uma configuração padrão
        config = [{
            'nome_pagina': 'Exemplo',
            'url': 'https://www.linkedin.com/company/example/',
            'xpath': '//*[@class="org-top-card-summary__follower-count"]'
        }]
        
        # Salvar como JSON para uso futuro
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("Arquivo config.json padrão criado")
        return pd.DataFrame(config)

def salvar_resultados(resultados_df):
    """Salva os resultados em múltiplos formatos"""
    # Salvar em Excel
    print("Salvando resultados em resultados.xlsx")
    resultados_df.to_excel('resultados.xlsx', index=False)
    
    # Salvar em CSV
    print("Salvando resultados em resultados.csv")
    resultados_df.to_csv('resultados.csv', index=False)
    
    # Salvar últimos resultados como uma tabela Markdown
    print("Salvando últimos resultados em relatorio.md")
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    ultimos_resultados = resultados_df[resultados_df['data'] == data_hoje]
    
    with open('relatorio.md', 'w', encoding='utf-8') as f:
        f.write(f"# Relatório de Seguidores - {data_hoje}\n\n")
        
        # Adicionar tabela Markdown
        if not ultimos_resultados.empty:
            f.write("| Nome | Seguidores |\n")
            f.write("|------|------------|\n")
            for _, row in ultimos_resultados.iterrows():
                f.write(f"| {row['nome']} | {row['seguidores']} |\n")
        else:
            f.write("Nenhum dado coletado hoje.\n")
        
        # Adicionar histórico recente (últimos 7 dias)
        f.write("\n## Histórico Recente\n\n")
        # Obter datas únicas em ordem decrescente
        datas_unicas = sorted(resultados_df['data'].unique(), reverse=True)[:7]
        
        if len(datas_unicas) > 0:
            # Criar tabela para cada página com evolução nos últimos dias
            for nome in resultados_df['nome'].unique():
                f.write(f"\n### {nome}\n\n")
                f.write("| Data | Seguidores |\n")
                f.write("|------|------------|\n")
                
                for data in datas_unicas:
                    linha = resultados_df[(resultados_df['data'] == data) & (resultados_df['nome'] == nome)]
                    if not linha.empty:
                        f.write(f"| {data} | {linha.iloc[0]['seguidores']} |\n")
        else:
            f.write("Sem dados históricos disponíveis.\n")
    
    print(f"Dados salvos em múltiplos formatos - {len(resultados_df)} registros totais")

def coletar_dados():
    """Função principal para coleta de dados"""
    print("Iniciando coleta de dados")
    
    try:
        # Carregar configuração
        dados = carregar_configuracao()
        print(f"Configuração carregada: {len(dados)} registros")
        
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
                    time.sleep(5)  # Aguardar carregamento
                    
                    # Pressionar ESC para fechar possíveis popups
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                    
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
                        # Adiciona entrada com erro para manter registro
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'seguidores': 0  # Valor padrão quando há erro
                        })
                
                except Exception as e:
                    print(f"Erro ao processar {nome_pagina}: {str(e)}")
                
                # Esperar entre requisições para evitar sobrecarga
                time.sleep(random.uniform(2, 5))
        
        finally:
            print("Finalizando o WebDriver")
            driver.quit()
        
        # Garantir que o arquivo de resultados seja criado mesmo se não houver dados novos
        if not novos_resultados:
            print("Nenhum novo resultado coletado")
            # Adicionar um registro vazio para garantir que o arquivo seja criado
            novos_resultados.append({
                'data': data_hoje,
                'nome': 'sem_dados',
                'seguidores': 0
            })
        
        # Converter para DataFrame
        novos_df = pd.DataFrame(novos_resultados)
        
        # Atualizar registros existentes do mesmo dia ou adicionar novos
        if not resultados_df.empty:
            # Para cada novo resultado...
            for _, nova_linha in novos_df.iterrows():
                # Verificar se já existe um registro para este nome_pagina na mesma data
                mask = (resultados_df['data'] == nova_linha['data']) & (resultados_df['nome'] == nova_linha['nome'])
                
                if mask.any():
                    # Se já existe, atualiza o valor de seguidores
                    print(f"Atualizando registro existente para {nova_linha['nome']} em {nova_linha['data']}")
                    resultados_df.loc[mask, 'seguidores'] = nova_linha['seguidores']
                else:
                    # Se não existe, adiciona a nova linha
                    print(f"Adicionando novo registro para {nova_linha['nome']} em {nova_linha['data']}")
                    resultados_df = pd.concat([resultados_df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            # Se o DataFrame de resultados estiver vazio, use os novos resultados diretamente
            resultados_df = novos_df
        
        # Ordenar por data (mais recente primeiro) e nome
        resultados_df = resultados_df.sort_values(['data', 'nome'], ascending=[False, True])
        
        # Salvar resultados em múltiplos formatos
        salvar_resultados(resultados_df)
        
    except Exception as e:
        print(f"Erro geral: {str(e)}")
        print(traceback.format_exc())
        # Garantir que o arquivo de resultados exista mesmo em caso de erro fatal
        if not os.path.exists('resultados.xlsx'):
            df_vazio = pd.DataFrame(columns=['data', 'nome', 'seguidores'])
            salvar_resultados(df_vazio)
            print("Criados arquivos vazios devido a erro")

if __name__ == "__main__":
    try:
        print("Iniciando script de coleta")
        coletar_dados()
        print("Script de coleta concluído com sucesso")
    except Exception as e:
        print(f"Erro geral no script: {str(e)}")
        print(traceback.format_exc())
        # Garantir que os arquivos de resultados existam mesmo em caso de erro fatal
        if not os.path.exists('resultados.xlsx'):
            df_vazio = pd.DataFrame(columns=['data', 'nome', 'seguidores'])
            salvar_resultados(df_vazio)
            print("Criados arquivos vazios devido a erro")
