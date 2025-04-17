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
    """Configura e retorna uma instância do ChromeDriver com configurações anti-detecção avançadas"""
    logging.info("Configurando o ChromeDriver com proteções anti-detecção avançadas")
    options = Options()
    
    # Headless pode ser detectado por alguns sites, mas é necessário no GitHub Actions
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Tamanho de tela aleatório para evitar detecção
    screen_width = random.randint(1050, 1200)
    screen_height = random.randint(800, 1000)
    options.add_argument(f"--window-size={screen_width},{screen_height}")
    logging.info(f"Usando resolução de tela: {screen_width}x{screen_height}")
    
    # Adicionar user-agents mais realistas e rotação
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]
    chosen_user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={chosen_user_agent}")
    logging.info(f"Usando user-agent: {chosen_user_agent}")
    
    # Configurações avançadas para evitar detecção
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Configurações adicionais anti-fingerprinting
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    
    # Adicionar parâmetros de idioma aleatórios
    languages = ["en-US,en;q=0.9", "pt-BR,pt;q=0.9,en;q=0.8", "es-ES,es;q=0.9,en;q=0.8"]
    options.add_argument(f"--lang={random.choice(languages)}")
    
    # Configurar timezone aleatória plausível
    timezones = ["America/Sao_Paulo", "America/New_York", "Europe/London", "Europe/Paris"]
    options.add_argument(f"--timezone={random.choice(timezones)}")
    
    # Adicionar outros headers HTTP para parecer mais humano
    options.add_argument("--accept-lang=en-US,en;q=0.9,pt;q=0.8")
    
    # Desabilitar imagens para carregar mais rápido (opcional, mas pode ser detectável)
    # Comentado para reduzir chance de detecção
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # options.add_experimental_option("prefs", prefs)
    
    # Configurações de cache e cookies para parecer mais humano
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.cookies": 2,
        "profile.cookie_controls_mode": 0,
        "profile.block_third_party_cookies": False,
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False,
        "profile.default_content_setting_values.plugins": 1
    }
    options.add_experimental_option("prefs", prefs)
    
    # No GitHub Actions, use o Chrome já instalado
    try:
        logging.info("Tentando usar o Chrome instalado no ambiente...")
        driver = webdriver.Chrome(options=options)
        
        # Executar JavaScript para mascarar ainda mais a automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": chosen_user_agent})
        
        # Scripts adicionais para mascarar a automação
        anti_bot_scripts = [
            # Falsificar propriedades do navegador para evitar detecção
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: function() { 
                return [
                    {description: "Chrome PDF Plugin", filename: "internal-pdf-viewer", name: "Chrome PDF Plugin", MimeTypes: []},
                    {description: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", name: "Chrome PDF Viewer", MimeTypes: []},
                    {description: "Native Client", filename: "internal-nacl-plugin", name: "Native Client", MimeTypes: []}
                ]; 
            }});
            """,
            
            # Adicionar propriedades de hardware que bots normalmente não têm
            """
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            """,
            
            # Falsificar técnicas de detecção de canvas fingerprinting
            """
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 16 && this.height === 16) {
                    // Provavelmente uma detecção de fingerprint
                    return originalToDataURL.apply(this, arguments);
                }
                return originalToDataURL.apply(this, arguments);
            };
            """
        ]
        
        # Executar scripts anti-detecção
        for script in anti_bot_scripts:
            driver.execute_script(script)
        
        # Modificar navigator.languages para parecer mais humano
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'pt-BR', 'pt'],
            });
            """
        })
        
        # Máscara WebGL fingerprinting
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            """
        })
        
        logging.info("Chrome inicializado com sucesso e configurações anti-detecção aplicadas")
        return driver
    except Exception as e:
        logging.error(f"Erro ao usar Chrome instalado: {str(e)}")
        logging.info("Tentando com ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Executar JavaScript para mascarar ainda mais a automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": chosen_user_agent})
        
        # Aplicar os mesmos scripts anti-detecção
        for script in anti_bot_scripts:
            driver.execute_script(script)
            
        # Aplicar as mesmas modificações de navigator e WebGL
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'pt-BR', 'pt'],
            });
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            """
        })
        
        logging.info("Chrome inicializado com ChromeDriverManager e configurações anti-detecção aplicadas")
        return driver

def extrair_seguidores(texto):
    """Extrai o número de seguidores do texto com melhorias"""
    if not texto:
        return None
        
    # Registra o texto para debugging
    logging.info(f"Texto para extração: '{texto}'")
    
    # Tentar formatos comuns com vários padrões
    patterns = [
        # Padrões em português
        r'([\d.,]+)\s*(?:seguidores|seguidor)',  
        r'([\d.,]+)[Kk]\s*(?:seguidores|seguidor)',  # Para formato 10K seguidores
        r'([\d.,]+)[Mm]\s*(?:seguidores|seguidor)',  # Para formato 1M seguidores
        
        # Padrões em inglês
        r'([\d.,]+)\s*(?:followers|follower)',
        r'([\d.,]+)[Kk]\s*(?:followers|follower)',
        r'([\d.,]+)[Mm]\s*(?:followers|follower)',
        
        # Padrões genéricos para qualquer texto após número
        r'([\d.,]+)[Kk]',  # 10K format
        r'([\d.,]+)[Mm]',  # 1M format
        r'([\d.,]+)\s*\w+',  # Qualquer texto após número
        r'([\d.,]+)',      # Apenas números
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto)
        if match:
            logging.info(f"Padrão encontrado: {pattern}")
            seguidores_texto = match.group(1).replace('.', '').replace(',', '')
            
            # Converter para número
            try:
                seguidores = int(seguidores_texto)
                
                # Verificar se é um formato abreviado (K ou M)
                if 'k' in texto.lower() or 'K' in texto:
                    seguidores *= 1000
                elif 'm' in texto.lower() or 'M' in texto:
                    seguidores *= 1000000
                
                logging.info(f"Seguidores extraídos: {seguidores}")
                return seguidores
            except ValueError:
                logging.warning(f"Não foi possível converter '{seguidores_texto}' para número")
    
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
        # Estratégias para LinkedIn (mantidas como estão, pois funcionam bem)
        try:
            # Estratégias existentes para LinkedIn...
            pass
                
        except Exception as e:
            logging.error(f"Erro ao buscar elemento alternativo para LinkedIn: {str(e)}")
    
    elif rede.lower() == "instagram":
        # Estratégias atualizadas para Instagram
        try:
            # Estratégia 1: Selecionar meta tags para contagem de seguidores (técnica moderna)
            script = """
            return document.querySelector('meta[property="og:description"]')?.content ||
                   document.querySelector('meta[name="description"]')?.content || "";
            """
            meta_content = driver.execute_script(script)
            logging.info(f"Meta content: {meta_content}")
            if meta_content:
                seguidores = extrair_seguidores(meta_content)
                if seguidores:
                    return seguidores
            
            # Estratégia 2: Selecionar elementos baseados nos novos seletores de 2025
            novos_seletores = [
                "section main header section ul li:nth-child(2)",  # Novo padrão 2023-2025
                "span._ac2a", # Classe usada na contagem de seguidores 2024-2025
                "span[title*='seguidores']", # Seletor por atributo title
                "a[href$='/followers/'] span", # Link para seguidores
                "header section ul li span span", # Estrutura geral
            ]
            
            for seletor in novos_seletores:
                try:
                    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                    for elemento in elementos:
                        texto = elemento.text or elemento.get_attribute("textContent")
                        logging.info(f"Elemento encontrado com seletor '{seletor}': '{texto}'")
                        seguidores = extrair_seguidores(texto)
                        if seguidores:
                            return seguidores
                except Exception as e:
                    logging.info(f"Seletor '{seletor}' falhou: {str(e)}")
            
            # Estratégia 3: Usar JavaScript para extração direta dos números
            scripts_js = [
                # Script que tenta encontrar números seguidos da palavra "seguidores" ou "followers"
                """
                const elements = document.querySelectorAll('*');
                for (const el of elements) {
                    const text = el.textContent || el.innerText;
                    if ((text && (text.includes('seguidores') || text.includes('followers'))) && 
                        /[0-9]/.test(text)) {
                        return text;
                    }
                }
                return "";
                """,
                # Script que busca qualquer número que possa representar seguidores
                """
                const mainHeader = document.querySelector('header');
                if (mainHeader) {
                    const lis = mainHeader.querySelectorAll('li');
                    for (const li of lis) {
                        const text = li.textContent || li.innerText;
                        if (text && /[0-9]/.test(text)) {
                            return text;
                        }
                    }
                }
                return "";
                """
            ]
            
            for script in scripts_js:
                try:
                    resultado = driver.execute_script(script)
                    logging.info(f"Resultado do script JavaScript: '{resultado}'")
                    if resultado:
                        seguidores = extrair_seguidores(resultado)
                        if seguidores:
                            return seguidores
                except Exception as e:
                    logging.info(f"Script JavaScript falhou: {str(e)}")
            
            # Estratégia 4: Tentar extrair informações das próprias métricas expostas pelo Instagram
            try:
                # Instagram expõe algumas métricas pelo GraphQL, podemos tentar extrair
                # Isso vai procurar no código fonte da página por dados JSON que possam conter a contagem
                html_completo = driver.page_source
                # Salvar HTML para análise manual
                with open(f"debug_{nome_pagina}_instagram_full.html", "w", encoding="utf-8") as f:
                    f.write(html_completo)
                
                # Padrões para encontrar JSON embutido que pode conter informações de seguidores
                json_patterns = [
                    r'window\._sharedData\s*=\s*({.*?});</script>',
                    r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
                    r'"userInfo".*?"followers":\s*(\d+)',
                    r'"follower_count":\s*(\d+)',
                    r'"followers":\s*"([^"]+)"',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, html_completo)
                    if matches:
                        logging.info(f"Match encontrado com padrão '{pattern}': {matches}")
                        for match in matches:
                            if isinstance(match, str) and match.isdigit():
                                return int(match)
                            elif isinstance(match, tuple) and len(match) > 0 and str(match[0]).isdigit():
                                return int(match[0])
                            # Tentar extrair número de string que não é totalmente numérica
                            elif isinstance(match, str):
                                seguidores = extrair_seguidores(match)
                                if seguidores:
                                    return seguidores
            except Exception as e:
                logging.error(f"Erro ao tentar extrair dados JSON/GraphQL: {str(e)}")
                    
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
            # Tentar fechar todos os possíveis popups do Instagram (2023-2025)
            popups_botoes = [
                # Botões de cookies
                "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Aceitar')]",
                "//button[contains(@class, 'glBry') and contains(text(), 'Accept')]",
                "//button[contains(@class, '_a9_1')]",
                
                # Botões de login/signup
                "//button[contains(text(), 'Not Now') or contains(text(), 'Agora não')]",
                "//button[contains(@class, '_a9-- _ap36')]",
                "//button[contains(@class, '_a9--')]",
                
                # Botões de notificação
                "//button[contains(text(), 'Not Now') or contains(text(), 'Cancel') or contains(text(), 'Cancelar')]",
            ]
            
            for xpath in popups_botoes:
                try:
                    botoes = driver.find_elements(By.XPATH, xpath)
                    for botao in botoes:
                        if botao.is_displayed():
                            botao.click()
                            logging.info(f"Botão fechado usando xpath: {xpath}")
                            time.sleep(1)
                except Exception as e:
                    logging.info(f"Não foi possível clicar no botão com xpath {xpath}: {str(e)}")
            
            # Usando JavaScript para fechar popups também
            popup_scripts = [
                # Fechar banner de cookies
                """
                const cookieBtns = Array.from(document.querySelectorAll('button')).filter(
                    btn => ['Accept', 'Allow', 'Aceitar', 'Concordar'].some(
                        text => (btn.textContent || '').includes(text)
                    )
                );
                if (cookieBtns.length > 0) cookieBtns[0].click();
                """,
                
                # Fechar dialog de login
                """
                const loginBtns = Array.from(document.querySelectorAll('button')).filter(
                    btn => ['Not Now', 'Agora não', 'Cancel', 'Cancelar'].some(
                        text => (btn.textContent || '').includes(text)
                    )
                );
                if (loginBtns.length > 0) loginBtns[0].click();
                """
            ]
            
            for script in popup_scripts:
                try:
                    driver.execute_script(script)
                    time.sleep(1)
                except Exception as e:
                    logging.info(f"Script para fechar popup falhou: {str(e)}")
    
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
