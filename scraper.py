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
    """Configura e retorna uma instância do ChromeDriver com configurações anti-detecção"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Configurações adicionais para evitar detecção como bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent de um navegador comum
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    
    # No GitHub Actions, use o Chrome já instalado
    try:
        print("Usando o Chrome instalado no ambiente...")
        driver = webdriver.Chrome(options=options)
        
        # Executar JavaScript para ocultar automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Erro ao usar Chrome instalado: {str(e)}")
        print("Tentando com ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Executar JavaScript para ocultar automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

def extrair_seguidores(texto, rede):
    """Extrai o número de seguidores do texto, considerando a rede social"""
    print(f"Texto para extração ({rede}): '{texto}'")
    
    # Remover pontos e espaços extras
    texto = texto.strip()
    
    # Padrões específicos para cada rede social
    padroes_por_rede = {
        'LinkedIn': [
            r'([\d.,]+)\s*seguidores',
            r'([\d.,]+)\s*followers',
            r'([\d\s.,]+)'  # Captura qualquer número
        ],
        'Instagram': [
            r'([\d.,]+)\s*seguidores',
            r'([\d.,]+)\s*followers',
            r'([\d.,]+)K',  # Formato abreviado com K
            r'([\d.,]+)M',  # Formato abreviado com M
            r'([\d\s.,]+)'  # Captura qualquer número
        ],
        'Twitter': [
            r'([\d.,]+)\s*seguidores',
            r'([\d.,]+)\s*followers',
            r'([\d.,]+)K',
            r'([\d.,]+)M',
            r'([\d\s.,]+)'
        ],
        'Facebook': [
            r'([\d.,]+)\s*seguidores',
            r'([\d.,]+)\s*followers',
            r'([\d.,]+)\s*curtidas',
            r'([\d.,]+)\s*likes',
            r'([\d\s.,]+)'
        ],
        'YouTube': [
            r'([\d.,]+)\s*inscritos',
            r'([\d.,]+)\s*subscribers',
            r'([\d.,]+)K',
            r'([\d.,]+)M',
            r'([\d\s.,]+)'
        ]
    }
    
    # Usar padrões específicos da rede se disponíveis, ou padrões genéricos
    padroes = padroes_por_rede.get(rede, [
        r'([\d.,]+)\s*seguidores',
        r'([\d.,]+)\s*followers',
        r'([\d.,]+)K',
        r'([\d.,]+)M',
        r'([\d\s.,]+)'
    ])
    
    # Tentar extrair usando os padrões
    for pattern in padroes:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            print(f"Padrão encontrado ({pattern}): {match.group(1)}")
            valor = match.group(1).replace('.', '').replace(',', '').replace(' ', '')
            
            # Se tiver K ou M no padrão (formato abreviado)
            if 'K' in pattern:
                return int(float(valor) * 1000)
            elif 'M' in pattern:
                return int(float(valor) * 1000000)
            
            return int(valor)
    
    # Tentar encontrar qualquer número no texto como último recurso
    numeros = re.findall(r'\d+', texto)
    if numeros:
        print(f"Encontrado número como último recurso: {numeros[0]}")
        return int(numeros[0])
    
    print("Nenhum padrão de seguidores encontrado no texto")
    return None

def processar_pagina(driver, url, xpath, rede):
    """Processa uma página específica e extrai o número de seguidores"""
    print(f"Acessando URL: {url}")
    
    # Limpar cookies e cache para evitar problemas de sessão
    driver.delete_all_cookies()
    
    # Acessar a URL
    driver.get(url)
    
    # Tempo de espera adaptativo com base na rede
    tempos_de_espera = {
        'LinkedIn': 10,
        'Instagram': 15,
        'Twitter': 8,
        'Facebook': 12,
        'YouTube': 8
    }
    tempo_espera = tempos_de_espera.get(rede, 10)
    
    print(f"Aguardando carregamento da página ({tempo_espera}s)")
    time.sleep(tempo_espera)
    
    # Pressionar ESC para fechar possíveis popups
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    
    # Estratégias específicas por rede social
    if rede == 'Instagram':
        # Rolar a página para garantir carregamento dos elementos
        driver.execute_script("window.scrollTo(0, 200)")
        time.sleep(2)
    
    # Tentar diferentes estratégias de extração
    try:
        # 1. Tentar o XPath fornecido
        print(f"Tentando encontrar elemento com XPath: {xpath}")
        elemento = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        texto = elemento.text
        print(f"Texto encontrado via XPath: '{texto}'")
        
        seguidores = extrair_seguidores(texto, rede)
        if seguidores:
            return seguidores
    except Exception as e:
        print(f"Erro ao buscar via XPath: {str(e)}")
    
    # 2. Tentar XPaths alternativos específicos para cada rede
    xpaths_alternativos = {
        'LinkedIn': [
            '//span[contains(@class, "follower-count")]',
            '//span[contains(text(), "seguidores")]',
            '//span[contains(text(), "followers")]'
        ],
        'Instagram': [
            '//section/ul/li[2]/a/span',
            '//section/ul/li[2]/span/span',
            '//div[contains(@class, "followers")]',
            '/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/header/section/ul/li[2]/a/span'
        ],
        'Twitter': [
            '//span[contains(text(), "seguidores")]/span',
            '//span[contains(text(), "followers")]/span'
        ],
        'Facebook': [
            '//span[contains(text(), "seguidores")]/span',
            '//span[contains(text(), "curtidas")]/span'
        ],
        'YouTube': [
            '//yt-formatted-string[@id="subscriber-count"]'
        ]
    }
    
    for xpath_alt in xpaths_alternativos.get(rede, []):
        try:
            print(f"Tentando XPath alternativo: {xpath_alt}")
            elemento = driver.find_element(By.XPATH, xpath_alt)
            texto = elemento.text
            print(f"Texto encontrado via XPath alternativo: '{texto}'")
            
            seguidores = extrair_seguidores(texto, rede)
            if seguidores:
                return seguidores
        except Exception as e:
            print(f"Erro com XPath alternativo: {str(e)}")
    
    # 3. Buscar no código-fonte da página
    print("Tentando extrair do código-fonte da página")
    page_source = driver.page_source
    
    # Padrões específicos para buscar no código-fonte
    padroes_html = {
        'LinkedIn': [
            r'followerCount":(\d+)',
            r'followers":(\d+)',
            r'seguidores">([^<]+)'
        ],
        'Instagram': [
            r'"edge_followed_by":{"count":(\d+)}',
            r'"followers":(\d+)',
            r'seguidores">([^<]+)'
        ],
        'Twitter': [
            r'"followers_count":(\d+)',
            r'seguidores">([^<]+)'
        ],
        'Facebook': [
            r'"followers":(\d+)',
            r'seguidores">([^<]+)'
        ],
        'YouTube': [
            r'"subscriberCountText":{"simpleText":"([^"]+)"',
            r'"subscriberCount":(\d+)'
        ]
    }
    
    for pattern in padroes_html.get(rede, [r'"followers":(\d+)', r'seguidores">([^<]+)']):
        match = re.search(pattern, page_source)
        if match:
            print(f"Padrão encontrado no código-fonte: {pattern}")
            texto = match.group(1)
            print(f"Texto encontrado no código-fonte: '{texto}'")
            
            seguidores = extrair_seguidores(texto, rede)
            if seguidores:
                return seguidores
    
    print("Não foi possível extrair o número de seguidores após todas as tentativas")
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
            'rede': 'LinkedIn',
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
            f.write("| Nome | Rede | Seguidores |\n")
            f.write("|------|------|------------|\n")
            for _, row in ultimos_resultados.iterrows():
                f.write(f"| {row['nome']} | {row['rede']} | {row['seguidores']} |\n")
        else:
            f.write("Nenhum dado coletado hoje.\n")
        
        # Adicionar histórico recente (últimos 7 dias)
        f.write("\n## Histórico Recente\n\n")
        # Obter datas únicas em ordem decrescente
        datas_unicas = sorted(resultados_df['data'].unique(), reverse=True)[:7]
        
        if len(datas_unicas) > 0:
            # Agrupar por rede social
            for rede in resultados_df['rede'].unique():
                f.write(f"\n### {rede}\n\n")
                
                # Criar tabela para cada página com evolução nos últimos dias
                for nome in resultados_df[resultados_df['rede'] == rede]['nome'].unique():
                    f.write(f"\n#### {nome}\n\n")
                    f.write("| Data | Seguidores |\n")
                    f.write("|------|------------|\n")
                    
                    for data in datas_unicas:
                        linha = resultados_df[(resultados_df['data'] == data) & 
                                             (resultados_df['nome'] == nome) & 
                                             (resultados_df['rede'] == rede)]
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
            
            # Verificar se o campo 'rede' existe, caso contrário adicionar
            if 'rede' not in resultados_df.columns:
                print("Adicionando coluna 'rede' aos resultados existentes")
                resultados_df['rede'] = 'Desconhecida'
        else:
            print("Criando novo DataFrame de resultados")
            resultados_df = pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores'])
        
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
                    # Verificar se o campo 'rede' existe
                    rede = linha['rede'] if 'rede' in linha else 'Desconhecida'
                    url = linha['url']
                    xpath = linha['xpath']
                    
                    print(f"Processando: {nome_pagina} ({rede}), URL: {url}")
                    
                    # Usar a função específica para processar a página
                    seguidores = processar_pagina(driver, url, xpath, rede)
                    
                    if seguidores:
                        print(f"Seguidores extraídos para {nome_pagina}: {seguidores}")
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'rede': rede,
                            'seguidores': seguidores
                        })
                    else:
                        print(f"Não foi possível extrair número de seguidores para {nome_pagina}")
                        # Adiciona entrada com valor nulo para manter registro
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'rede': rede,
                            'seguidores': 0  # Valor padrão quando não consegue extrair
                        })
                
                except Exception as e:
                    print(f"Erro ao processar {nome_pagina}: {str(e)}")
                    print(traceback.format_exc())
                    
                    # Adicionar ao resultado mesmo com erro
                    novos_resultados.append({
                        'data': data_hoje,
                        'nome': nome_pagina,
                        'rede': rede if 'rede' in locals() else 'Desconhecida',
                        'seguidores': 0  # Valor padrão quando há erro
                    })
                
                # Esperar entre requisições para evitar sobrecarga
                tempo_espera = random.uniform(3, 7)  # Aumentado para evitar detecção
                print(f"Aguardando {tempo_espera:.2f}s antes da próxima requisição")
                time.sleep(tempo_espera)
        
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
                'rede': 'Desconhecida',
                'seguidores': 0
            })
        
        # Converter para DataFrame
        novos_df = pd.DataFrame(novos_resultados)
        
        # Atualizar registros existentes do mesmo dia ou adicionar novos
        if not resultados_df.empty:
            # Para cada novo resultado...
            for _, nova_linha in novos_df.iterrows():
                # Verificar se já existe um registro para este nome_pagina e rede na mesma data
                mask = ((resultados_df['data'] == nova_linha['data']) & 
                        (resultados_df['nome'] == nova_linha['nome']) & 
                        (resultados_df['rede'] == nova_linha['rede']))
                
                if mask.any():
                    # Se já existe, atualiza o valor de seguidores
                    print(f"Atualizando registro existente para {nova_linha['nome']} ({nova_linha['rede']}) em {nova_linha['data']}")
                    resultados_df.loc[mask, 'seguidores'] = nova_linha['seguidores']
                else:
                    # Se não existe, adiciona a nova linha
                    print(f"Adicionando novo registro para {nova_linha['nome']} ({nova_linha['rede']}) em {nova_linha['data']}")
                    resultados_df = pd.concat([resultados_df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            # Se o DataFrame de resultados estiver vazio, use os novos resultados diretamente
            resultados_df = novos_df
        
        # Ordenar por data (mais recente primeiro), rede e nome
        resultados_df = resultados_df.sort_values(['data', 'rede', 'nome'], ascending=[False, True, True])
        
        # Salvar resultados em múltiplos formatos
        salvar_resultados(resultados_df)
        
    except Exception as e:
        print(f"Erro geral: {str(e)}")
        print(traceback.format_exc())
        # Garantir que o arquivo de resultados exista mesmo em caso de erro fatal
        if not os.path.exists('resultados.xlsx'):
            df_vazio = pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores'])
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
            df_vazio = pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores'])
            salvar_resultados(df_vazio)
            print("Criados arquivos vazios devido a erro")
