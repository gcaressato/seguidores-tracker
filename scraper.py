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
import random  # Adicionado importação no topo
from datetime import datetime

def configurar_driver():
  """Configura e retorna uma instância do ChromeDriver"""
  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--window-size=1920,1080")
  options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
  
  service = Service(ChromeDriverManager().install())
  driver = webdriver.Chrome(service=service, options=options)
  return driver

def extrair_seguidores(texto):
  """Extrai o número de seguidores do texto"""
  # Pattern para encontrar números seguidos pela palavra "seguidores"
  # Lida com formatos como "298.749 seguidores" ou "1.234 seguidores"
  pattern = r'([\d.,]+)\s+seguidores'
  match = re.search(pattern, texto)
  
  if match:
      # Remove pontos e converte para inteiro
      seguidores = match.group(1).replace('.', '').replace(',', '')
      return int(seguidores)
  
  return None

def coletar_dados():
  """Função principal para coleta de dados"""
  # Verificar se o arquivo de configuração existe
  if not os.path.exists('config.xlsx'):
      print("Arquivo config.xlsx não encontrado!")
      return
  
  # Carregar dados do Excel
  dados = pd.read_excel('config.xlsx')
  
  # Verificar se o arquivo de resultados existe, senão criar
  if os.path.exists('resultados.xlsx'):
      resultados_df = pd.read_excel('resultados.xlsx')
  else:
      resultados_df = pd.DataFrame(columns=['data', 'nome', 'seguidores'])
  
  # Data atual
  data_hoje = datetime.now().strftime("%Y-%m-%d")
  
  # Inicializar o driver
  driver = configurar_driver()
  
  # Lista para armazenar novos resultados
  novos_resultados = []
  
  try:
      for _, linha in dados.iterrows():
          nome_pagina = linha['nome_pagina']
          url = linha['url']
          xpath = linha['xpath']
          
          print(f"Processando: {nome_pagina}")
          
          try:
              # Acessar a URL
              driver.get(url)
              time.sleep(3)  # Aguardar carregamento inicial
              
              # Pressionar ESC para fechar possíveis popups
              webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
              time.sleep(1)
              
              # Encontrar o elemento usando XPath
              elemento = WebDriverWait(driver, 10).until(
                  EC.presence_of_element_located((By.XPATH, xpath))
              )
              
              # Extrair o texto e buscar o número de seguidores
              texto_elemento = elemento.text
              seguidores = extrair_seguidores(texto_elemento)
              
              if seguidores:
                  print(f"- {nome_pagina}: {seguidores} seguidores")
                  novos_resultados.append({
                      'data': data_hoje,
                      'nome': nome_pagina,
                      'seguidores': seguidores
                  })
              else:
                  print(f"- Não foi possível extrair número de seguidores para {nome_pagina}")
              
          except Exception as e:
              print(f"Erro ao processar {nome_pagina}: {str(e)}")
          
          # Esperar entre requisições para evitar sobrecarga
          time.sleep(random.uniform(2, 5))
  
  finally:
      driver.quit()
  
  # Adicionar novos resultados ao DataFrame
  if novos_resultados:
      novos_df = pd.DataFrame(novos_resultados)
      resultados_df = pd.concat([resultados_df, novos_df], ignore_index=True)
      
      # Salvar resultados atualizados
      resultados_df.to_excel('resultados.xlsx', index=False)
      print(f"Dados salvos em resultados.xlsx")

if __name__ == "__main__":
  coletar_dados()  # Removida importação interna de random
