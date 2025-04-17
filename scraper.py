import pandas as pd
import re
import json
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
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def configurar_driver():
    """Configura e retorna uma instância do ChromeDriver com configurações anti-detecção"""
    logging.info("Configurando o ChromeDriver")
    options = Options()
    
    # Headless pode ser detectado por alguns sites, mas é necessário no GitHub Actions
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Adicionar user-agents mais realistas e rotação
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ]
    chosen_user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={chosen_user_agent}")
    logging.info(f"Usando user-agent: {chosen_user_agent}")
    
    # Configurações adicionais para evitar detecção
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Desabilitar imagens para carregar mais rápido
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    # No GitHub Actions, use o Chrome já instalado
    try:
        logging.info("Tentando usar o Chrome instalado no ambiente...")
        driver = webdriver.Chrome(options=options)
        
        # Executar JavaScript para mascarar ainda mais a automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": chosen_user_agent})
        
        logging.info("Chrome inicializado com sucesso")
        return driver
    except Exception as e:
        logging.error(f"Erro ao usar Chrome instalado: {str(e)}")
        logging.info("Tentando com ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Executar JavaScript para mascarar ainda mais a automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": chosen_user_agent})
        
        logging.info("Chrome inicializado com ChromeDriverManager")
        return driver

def extrair_seguidores(texto):
    """Extrai o número de seguidores do texto"""
    # Registra o texto para debugging
    logging.info(f"Texto para extração: '{texto}'")
    
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
            logging.info(f"Padrão alternativo encontrado: {pattern}")
            seguidores = match.group(1).replace('.', '').replace(',', '')
            return int(seguidores)
    
    logging.warning("Nenhum padrão de seguidores encontrado no texto")
    return None

def tirar_screenshot(driver, nome_pagina):
    """Tira um screenshot da página atual e salva em um diretório"""
    try:
        # Criar diretório de screenshots se não existir
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        # Nome do arquivo com timestamp para evitar sobrescritas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/{nome_pagina}_{timestamp}.png"
        
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot salvo em {screenshot_path}")
    except Exception as e:
        logging.error(f"Erro ao tirar screenshot: {str(e)}")

def encontrar_elemento_alternativo(driver, nome_pagina, rede):
    """Tenta encontrar o elemento de contagem de seguidores usando diferentes métodos"""
    logging.info(f"Tentando encontrar elemento alternativo para {nome_pagina} na rede {rede}")
    
    # Estratégias específicas para cada rede social
    if rede.lower() == "linkedin":
        # Estratégias para LinkedIn
        try:
            # Estratégia 1: Buscar pelo texto que contém "followers" ou "seguidores"
            elementos = driver.find_elements(By.XPATH, "//*[contains(text(), 'followers') or contains(text(), 'seguidores')]")
            for elemento in elementos:
                texto = elemento.text
                logging.info(f"Elemento alternativo encontrado no LinkedIn: '{texto}'")
                seguidores = extrair_seguidores(texto)
                if seguidores:
                    return seguidores
            
            # Estratégia 2: Buscar pela classe que normalmente contém essa informação
            elementos = driver.find_elements(By.CSS_SELECTOR, ".org-top-card-summary__info-item")
            for elemento in elementos:
                texto = elemento.text
                logging.info(f"Elemento pela classe encontrado no LinkedIn: '{texto}'")
                seguidores = extrair_seguidores(texto)
                if seguidores:
                    return seguidores
                    
            # Estratégia 3: Extrair do HTML completo da página
            html_completo = driver.page_source
            match = re.search(r'([\d.,]+)\s+(?:followers|seguidores)', html_completo)
            if match:
                seguidores_texto = match.group(1).replace('.', '').replace(',', '')
                logging.info(f"Seguidores encontrados no HTML completo: {seguidores_texto}")
                return int(seguidores_texto)
                
        except Exception as e:
            logging.error(f"Erro ao buscar elemento alternativo para LinkedIn: {str(e)}")
    
    elif rede.lower() == "instagram":
        # Estratégias para Instagram
        try:
            # Estratégia 1: Usar seletores CSS mais robustos
            elementos = driver.find_elements(By.CSS_SELECTOR, "section main header section ul li")
            for elemento in elementos:
                texto = elemento.text
                if "seguidores" in texto.lower() or "followers" in texto.lower():
                    logging.info(f"Elemento alternativo encontrado no Instagram: '{texto}'")
                    seguidores = extrair_seguidores(texto)
                    if seguidores:
                        return seguidores
            
            # Estratégia 2: Buscar por atributo aria-label que contém a informação
            elementos = driver.find_elements(By.CSS_SELECTOR, "[aria-label*='followers'], [aria-label*='seguidores']")
            for elemento in elementos:
                texto = elemento.get_attribute("aria-label")
                logging.info(f"Elemento por aria-label encontrado no Instagram: '{texto}'")
                seguidores = extrair_seguidores(texto)
                if seguidores:
                    return seguidores
                    
            # Estratégia 3: Extrair usando regex do HTML completo
            html_completo = driver.page_source
            with open(f"debug_{nome_pagina}_html.txt", "w", encoding="utf-8") as f:
                f.write(html_completo)
            logging.info(f"HTML completo salvo em debug_{nome_pagina}_html.txt")
            
            match = re.search(r'([\d.,]+)\s+(?:followers|seguidores)', html_completo)
            if match:
                seguidores_texto = match.group(1).replace('.', '').replace(',', '')
                logging.info(f"Seguidores encontrados no HTML completo: {seguidores_texto}")
                return int(seguidores_texto)
                
        except Exception as e:
            logging.error(f"Erro ao buscar elemento alternativo para Instagram: {str(e)}")
    
    # Se nenhuma estratégia funcionou
    logging.warning(f"Não foi possível encontrar elementos alternativos para {nome_pagina}")
    return None

def lidar_com_cookies_e_popups(driver, rede):
    """Tenta lidar com cookies e popups de login comuns em redes sociais"""
    logging.info(f"Tentando lidar com cookies e popups para {rede}")
    
    try:
        if rede.lower() == "linkedin":
            # Tentar fechar banner de cookies do LinkedIn
            try:
                cookie_botoes = driver.find_elements(By.XPATH, "//button[contains(@class, 'artdeco-global-alert') or contains(@class, 'cookie-banner')]")
                for botao in cookie_botoes:
                    if "aceit" in botao.text.lower() or "concord" in botao.text.lower() or "accept" in botao.text.lower():
                        botao.click()
                        logging.info("Botão de cookies do LinkedIn clicado")
                        time.sleep(1)
                        break
            except:
                logging.info("Não encontrou ou não conseguiu clicar no botão de cookies do LinkedIn")
                
            # Tentar fechar modal de login
            try:
                login_botoes = driver.find_elements(By.XPATH, "//button[contains(@class, 'modal__dismiss') or contains(@aria-label, 'Dismiss')]")
                for botao in login_botoes:
                    botao.click()
                    logging.info("Modal de login do LinkedIn fechado")
                    time.sleep(1)
                    break
            except:
                logging.info("Não encontrou ou não conseguiu fechar modal de login do LinkedIn")
                
        elif rede.lower() == "instagram":
            # Tentar fechar banner de cookies do Instagram
            try:
                cookie_botoes = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Aceitar')]")
                for botao in cookie_botoes:
                    botao.click()
                    logging.info("Botão de cookies do Instagram clicado")
                    time.sleep(1)
                    break
            except:
                logging.info("Não encontrou ou não conseguiu clicar no botão de cookies do Instagram")
                
            # Tentar fechar modal de login do Instagram
            try:
                login_botoes = driver.find_elements(By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Agora não')]")
                for botao in login_botoes:
                    botao.click()
                    logging.info("Modal de login do Instagram fechado")
                    time.sleep(1)
                    break
            except:
                logging.info("Não encontrou ou não conseguiu fechar modal de login do Instagram")
        
        # Pressionar ESC como backup para fechar popups
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        
    except Exception as e:
        logging.error(f"Erro ao lidar com cookies e popups: {str(e)}")

def coletar_dados():
    """Função principal para coleta de dados"""
    logging.info("Iniciando coleta de dados")
    logging.info(f"Diretório atual: {os.getcwd()}")
    
    # Verificar se o arquivo de configuração existe
    if not os.path.exists('config.json'):
        logging.error("Arquivo config.json não encontrado!")
        # Criar um arquivo de resultados vazio para evitar falha no workflow
        pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores']).to_csv('resultados.csv', index=False)
        logging.info("Criado resultados.csv vazio")
        return
    
    # Carregar dados do JSON
    logging.info("Carregando dados do arquivo config.json")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            dados_json = json.load(f)
        
        # Converter para DataFrame para facilitar o processamento
        dados = pd.DataFrame(dados_json)
        logging.info(f"Dados carregados: {len(dados)} registros")
        logging.info(f"Colunas: {dados.columns.tolist()}")
    except Exception as e:
        logging.error(f"Erro ao carregar config.json: {str(e)}")
        # Criar um arquivo de resultados vazio para evitar falha no workflow
        pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores']).to_csv('resultados.csv', index=False)
        logging.info("Criado resultados.csv vazio")
        return
    
    # Verificar se o arquivo de resultados existe, senão criar
    if os.path.exists('resultados.csv'):
        logging.info("Carregando arquivo de resultados existente")
        resultados_df = pd.read_csv('resultados.csv')
        logging.info(f"Resultados carregados: {len(resultados_df)} registros")
    else:
        logging.info("Criando novo DataFrame de resultados")
        resultados_df = pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores'])
    
    # Data atual
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"Data de coleta: {data_hoje}")
    
    # Lista para armazenar novos resultados
    novos_resultados = []
    
    try:
        # Inicializar o driver
        logging.info("Inicializando o WebDriver")
        driver = configurar_driver()
        
        try:
            for i, linha in enumerate(dados_json):
                try:
                    nome_pagina = linha['nome_pagina']
                    rede = linha['rede']
                    url = linha['url']
                    xpath = linha['xpath']
                    
                    logging.info(f"Processando [{i+1}/{len(dados_json)}]: {nome_pagina}, Rede: {rede}, URL: {url}")
                    
                    # Acessar a URL com retry
                    max_tentativas = 3
                    for tentativa in range(max_tentativas):
                        try:
                            driver.get(url)
                            logging.info(f"Página carregada: {url} (tentativa {tentativa+1})")
                            break
                        except Exception as e:
                            logging.error(f"Erro ao carregar página (tentativa {tentativa+1}): {str(e)}")
                            if tentativa < max_tentativas - 1:
                                time.sleep(5)  # Espera antes de tentar novamente
                            else:
                                raise  # Re-lança a exceção se todas as tentativas falharem
                    
                    # Espera aleatória para simular comportamento humano
                    time.sleep(random.uniform(5, 10))
                    
                    # Lidar com cookies e popups
                    lidar_com_cookies_e_popups(driver, rede)
                    
                    # Tirar screenshot para debug
                    tirar_screenshot(driver, nome_pagina)
                    
                    seguidores = None
                    
                    # Tentar o XPath original
                    try:
                        logging.info(f"Buscando elemento com XPath: {xpath}")
                        elemento = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        
                        # Extrair o texto e buscar o número de seguidores
                        texto_elemento = elemento.text
                        logging.info(f"Texto encontrado: '{texto_elemento}'")
                        seguidores = extrair_seguidores(texto_elemento)
                        
                        if seguidores:
                            logging.info(f"Seguidores extraídos com XPath original para {nome_pagina}: {seguidores}")
                        else:
                            logging.warning(f"Não foi possível extrair seguidores do texto com XPath original")
                    except Exception as e:
                        logging.warning(f"XPath original falhou: {str(e)}")
                        
                    # Se o XPath original falhou, tentar métodos alternativos
                    if not seguidores:
                        logging.info("Tentando métodos alternativos para encontrar o número de seguidores")
                        seguidores = encontrar_elemento_alternativo(driver, nome_pagina, rede)
                        
                    # Gravar HTML para debug
                    with open(f"debug_{nome_pagina}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logging.info(f"HTML da página salvo em debug_{nome_pagina}.html")
                    
                    # Registrar o resultado
                    if seguidores:
                        logging.info(f"Seguidores extraídos para {nome_pagina}: {seguidores}")
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'rede': rede,
                            'seguidores': seguidores
                        })
                    else:
                        logging.warning(f"Não foi possível extrair número de seguidores para {nome_pagina}")
                        # Adiciona entrada com valor nulo para manter registro
                        novos_resultados.append({
                            'data': data_hoje,
                            'nome': nome_pagina,
                            'rede': rede,
                            'seguidores': 0  # Valor padrão quando não consegue extrair
                        })
                
                except Exception as e:
                    logging.error(f"Erro ao processar {nome_pagina}: {str(e)}")
                    logging.error(traceback.format_exc())
                    # Adiciona entrada com erro para manter registro
                    novos_resultados.append({
                        'data': data_hoje,
                        'nome': nome_pagina,
                        'rede': rede,
                        'seguidores': 0  # Valor padrão quando há erro
                    })
                
                # Esperar entre requisições para evitar sobrecarga
                # Tempo maior para evitar detecção de automação
                time.sleep(random.uniform(5, 10))
        
        finally:
            logging.info("Finalizando o WebDriver")
            driver.quit()
    
    except Exception as e:
        logging.error(f"Erro geral: {str(e)}")
        logging.error(traceback.format_exc())
    
    finally:
        # Garantir que o arquivo de resultados seja criado mesmo se não houver dados novos
        if not novos_resultados:
            logging.warning("Nenhum novo resultado coletado")
            # Adicionar um registro vazio para garantir que o arquivo seja criado
            novos_resultados.append({
                'data': data_hoje,
                'nome': 'sem_dados',
                'rede': 'sem_rede',
                'seguidores': 0
            })
        
        # Converter para DataFrame
        novos_df = pd.DataFrame(novos_resultados)
        
        # Atualizar registros existentes do mesmo dia ou adicionar novos
        # Esta é a parte chave para evitar duplicatas no mesmo dia
        if not resultados_df.empty:
            # Para cada novo resultado...
            for _, nova_linha in novos_df.iterrows():
                # Verificar se já existe um registro para este nome_pagina na mesma data
                mask = (resultados_df['data'] == nova_linha['data']) & (resultados_df['nome'] == nova_linha['nome'])
                
                if mask.any():
                    # Se já existe, atualiza o valor de seguidores
                    logging.info(f"Atualizando registro existente para {nova_linha['nome']} em {nova_linha['data']}")
                    resultados_df.loc[mask, 'seguidores'] = nova_linha['seguidores']
                    resultados_df.loc[mask, 'rede'] = nova_linha['rede']  # Atualiza rede também
                else:
                    # Se não existe, adiciona a nova linha
                    logging.info(f"Adicionando novo registro para {nova_linha['nome']} em {nova_linha['data']}")
                    resultados_df = pd.concat([resultados_df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            # Se o DataFrame de resultados estiver vazio, use os novos resultados diretamente
            resultados_df = novos_df
        
        # Ordenar por data (mais recente primeiro) e nome
        resultados_df = resultados_df.sort_values(['data', 'nome'], ascending=[False, True])
        
        # Salvar resultados atualizados
        logging.info("Salvando resultados em resultados.csv")
        resultados_df.to_csv('resultados.csv', index=False)
        logging.info(f"Dados salvos em resultados.csv - {len(resultados_df)} registros totais")

if __name__ == "__main__":
    try:
        logging.info("Iniciando script de coleta")
        coletar_dados()
        logging.info("Script de coleta concluído com sucesso")
    except Exception as e:
        logging.error(f"Erro geral no script: {str(e)}")
        logging.error(traceback.format_exc())
        # Garantir que o arquivo de resultados exista mesmo em caso de erro fatal
        if not os.path.exists('resultados.csv'):
            pd.DataFrame(columns=['data', 'nome', 'rede', 'seguidores']).to_csv('resultados.csv', index=False)
            logging.info("Criado resultados.csv vazio devido a erro")
