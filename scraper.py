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

# Configurar logging apenas para console (sem arquivo)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
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
        
        # Executar apenas os comandos básicos de mascaramento que sabemos que funcionam
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": chosen_user_agent})
        
        logging.info("Chrome inicializado com sucesso")
        return driver
    except Exception as e:
        logging.error(f"Erro ao usar Chrome instalado: {str(e)}")
        logging.info("Tentando com ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Executar apenas os comandos básicos de mascaramento que sabemos que funcionam
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
    """Função mantida para compatibilidade, mas não salva mais screenshots"""
    logging.info(f"Screenshot para {nome_pagina} desativado")

# ----- NOVOS MÉTODOS PARA INSTAGRAM -----

def extrair_seguidores_instagram_method1(driver, xpath):
    """Método 1: Usando o XPath fornecido."""
    try:
        # Usando o XPath fornecido
        followers_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        followers_text = followers_element.text
        
        # Tenta converter para número
        followers_count = ''.join(filter(str.isdigit, followers_text))
        if followers_count:
            followers_count = int(followers_count)
            return followers_count
        return None
        
    except Exception:
        return None

def extrair_seguidores_instagram_method2(driver):
    """Método 2: Usando seletores CSS mais genéricos."""
    try:
        # Tenta encontrar usando CSS Selector mais genérico
        css_selector = "section main header section ul li:nth-child(2) span"
        followers_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        
        followers_text = followers_element.text
        
        # Tenta converter para número
        followers_count = ''.join(filter(str.isdigit, followers_text))
        if followers_count:
            followers_count = int(followers_count)
            return followers_count
        return None
        
    except Exception:
        return None

def extrair_seguidores_instagram_method3(driver):
    """Método 3: Encontra elementos by aria-label."""
    try:
        # Localiza link/botão de seguidores pelo atributo aria-label
        elements = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'follower') or contains(@aria-label, 'seguidor')]")
        
        if not elements:
            return None
        
        for element in elements:
            aria_label = element.get_attribute("aria-label")
            
            # Extrai números do texto
            followers_count = ''.join(filter(str.isdigit, aria_label))
            if followers_count:
                try:
                    followers_count = int(followers_count)
                    return followers_count
                except ValueError:
                    continue
        
        return None
        
    except Exception:
        return None

def extrair_seguidores_instagram_method4(driver):
    """Método 4: Busca por texto contendo 'seguidores' ou 'followers'."""
    try:
        # Tenta encontrar qualquer elemento que contenha o texto 'seguidores' ou 'followers'
        elements = driver.find_elements(By.XPATH, 
                                       "//*[contains(text(), 'seguidores') or contains(text(), 'followers')]")
        
        if not elements:
            return None
        
        for element in elements:
            text = element.text
            
            # Se for apenas o texto "seguidores" ou "followers", tenta pegar o elemento pai
            if text.strip().lower() in ['seguidores', 'followers']:
                try:
                    parent = element.find_element(By.XPATH, "./..")
                    text = parent.text
                except:
                    pass
            
            # Extrai números do texto
            numbers = ''.join(filter(str.isdigit, text))
            if numbers:
                try:
                    followers_count = int(numbers)
                    return followers_count
                except ValueError:
                    continue
        
        return None
        
    except Exception:
        return None

def extrair_seguidores_instagram_method5(driver):
    """Método 5: Tentativa usando JavaScript para extrair dados da página."""
    logging.info("Tentando extrair seguidores via JavaScript (Método 5)")
    
    try:
        # Script JS otimizado para focar apenas em elementos menores que contêm dados de seguidores
        js_script = """
        const extractNumber = (text) => {
            if (!text) return null;
            const matches = text.match(/\\d+[.,]?\\d*/g);
            return matches ? matches.join('') : null;
        };
        
        // Busca mais focada em elementos específicos
        let results = [];
        
        // 1. Tenta elementos com os textos específicos de seguidores
        const targetTexts = ['seguidores', 'followers', 'seguidor'];
        for (const text of targetTexts) {
            const elements = document.querySelectorAll(`*:not(script):not(style)`);
            for (let i = 0; i < Math.min(elements.length, 100); i++) {
                const el = elements[i];
                if (el.textContent && el.textContent.toLowerCase().includes(text) && 
                    el.textContent.length < 100) {  // Limita tamanho do texto
                    results.push({
                        text: el.textContent.trim(),
                        number: extractNumber(el.textContent)
                    });
                }
            }
        }
        
        // 2. Tenta elementos específicos por seletores conhecidos do Instagram
        const selectors = [
            'section main header section ul li span', 
            'span._ac2a',
            'span[title]'
        ];
        
        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            for (let i = 0; i < elements.length; i++) {
                const el = elements[i];
                if (el.textContent && el.textContent.length < 50) {
                    results.push({
                        text: el.textContent.trim(),
                        number: extractNumber(el.textContent)
                    });
                }
            }
        }
        
        return JSON.stringify(results);
        """
        
        result = driver.execute_script(js_script)
        data = json.loads(result)
        
        # Filtra apenas os que têm números
        valid_data = [item for item in data if item.get('number')]
        
        if valid_data:
            # Log de amostra de dados encontrados (limitado a 3)
            for i, item in enumerate(valid_data[:3]):
                logging.info(f"Método 5 - Item {i+1}: Texto: {item['text']}")
            
            # Pega o primeiro número válido
            for item in valid_data:
                try:
                    if item['number'] and len(item['number']) < 10:  # Evita números gigantes
                        followers_count = int(item['number'].replace(',', '').replace('.', ''))
                        logging.info(f"Método 5 - Seguidores encontrados: {followers_count}")
                        return followers_count
                except (ValueError, TypeError):
                    continue
        
        logging.info("Método 5 - Nenhum número válido extraído")
        return None
        
    except Exception as e:
        logging.info(f"Método 5 - Erro: {str(e)}")
        return None

def extrair_seguidores_instagram(driver, xpath, nome_pagina):
    """
    Tenta extrair seguidores do Instagram usando múltiplos métodos.
    Retorna ao primeiro sinal de sucesso para otimizar o tempo de execução.
    """
    logging.info(f"Extraindo seguidores para {nome_pagina} (Instagram)")

    # Lista de métodos a serem tentados em ordem (do mais eficaz ao menos eficaz)
    metodos = [
        (extrair_seguidores_instagram_method2, [driver]),         # CSS Selector específico
        (extrair_seguidores_instagram_method1, [driver, xpath]),  # XPath fornecido
        (extrair_seguidores_instagram_method5, [driver]),         # JavaScript otimizado
        (extrair_seguidores_instagram_method4, [driver]),         # Busca por texto
        (extrair_seguidores_instagram_method3, [driver]),         # Aria-label (mais lento)
    ]
    
    # Tenta cada método até encontrar um que funcione
    for i, (metodo, args) in enumerate(metodos):
        try:
            logging.info(f"Método {i+1} para {nome_pagina}")
            seguidores = metodo(*args)
            if seguidores:
                logging.info(f"✅ Método {i+1}: {seguidores} seguidores")
                return seguidores
            logging.info(f"❌ Método {i+1}: Sem resultado")
        except Exception as e:
            logging.info(f"❌ Método {i+1}: Erro - {str(e)[:50] if str(e) else 'Erro desconhecido'}")
    
    logging.info(f"⚠️ Todos os métodos falharam para {nome_pagina}")
    return None

def lidar_com_cookies_instagram(driver):
    """Tenta lidar com diálogos de cookies e popups do Instagram"""
    logging.info("Tentando lidar com cookies e popups do Instagram")
    
    try:
        # Tenta fechar modal de cookies
        try:
            cookie_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Aceitar')]")
            for button in cookie_buttons:
                button.click()
                logging.info("Clicou em botão de cookies")
                time.sleep(2)
                break
        except:
            logging.info("Não encontrou ou não conseguiu clicar no botão de cookies")
        
        # Tenta fechar modal de login 
        try:
            close_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Fechar')]")
            for button in close_buttons:
                button.click()
                logging.info("Fechou modal de login")
                time.sleep(2)
                break
        except:
            logging.info("Não encontrou ou não conseguiu fechar modal de login")
        
        # Pressiona ESC como backup
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        
    except Exception as e:
        logging.error(f"Erro ao lidar com cookies e popups do Instagram: {str(e)}")

def encontrar_elemento_alternativo(driver, nome_pagina, rede):
    """Tenta encontrar o elemento de contagem de seguidores usando diferentes métodos"""
    logging.info(f"Tentando encontrar elemento alternativo para {nome_pagina} na rede {rede}")
    
    # Adiciona suporte específico para Instagram
    if rede.lower() == "instagram":
        # Essa função retorna None para indicar que o tratamento especializado será feito em outro lugar
        return None
    elif rede.lower() == "linkedin":
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
    
    # Se nenhuma estratégia funcionou
    logging.warning(f"Não foi possível encontrar elementos alternativos para {nome_pagina}")
    return None

def lidar_com_cookies_e_popups(driver, rede):
    """Tenta lidar com cookies e popups de login comuns em redes sociais"""
    logging.info(f"Tentando lidar com cookies e popups para {rede}")
    
    try:
        # Tratamento específico para Instagram
        if rede.lower() == "instagram":
            lidar_com_cookies_instagram(driver)
        elif rede.lower() == "linkedin":
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
                    
                    # Lógica específica para o Instagram
                    if rede.lower() == "instagram":
                        logging.info(f"Usando métodos especializados para Instagram: {nome_pagina}")
                        seguidores = extrair_seguidores_instagram(driver, xpath, nome_pagina)
                    else:
                        # Para outras redes, usa o método original
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
                    
                    # Não salva mais o HTML para debug
                    logging.info(f"Processamento de {nome_pagina} concluído")
                    
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
            # Manter apenas as entradas que não são da data atual
            resultados_atuais = resultados_df[resultados_df['data'] != data_hoje]
            
            # Verificar o que aconteceu com os dados antigos dessa data
            dados_mesma_data = resultados_df[resultados_df['data'] == data_hoje]
            if not dados_mesma_data.empty:
                logging.info(f"Removendo {len(dados_mesma_data)} registros antigos da data {data_hoje}")
            
            # Concatenar os resultados atuais (sem a data de hoje) com os novos resultados
            resultados_df = pd.concat([resultados_atuais, novos_df], ignore_index=True)
            logging.info(f"Atualizados registros para a data {data_hoje}: foram removidos registros antigos e adicionados {len(novos_df)} novos")
        else:
            # Se o DataFrame de resultados estiver vazio, use os novos resultados diretamente
            resultados_df = novos_df
            logging.info(f"Adicionados {len(novos_df)} registros para a data {data_hoje}")
        
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
