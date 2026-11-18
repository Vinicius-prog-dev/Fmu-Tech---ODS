# 🏥 Estoque Vital
<p align="left">
  <img src="assets/Logo do Estoque Vital.jpeg" alt="Logo do projeto Estoque Vital" width="300"/>
</p>
> **Inteligência de dados aplicada ao combate ao desperdício e ao desabastecimento de medicamentos essenciais na rede pública de saúde.**

![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-2E7D32?style=for-the-badge)
![ODS](https://img.shields.io/badge/ONU-ODS_3:_Saúde_e_Bem--Estar-1E88E5?style=for-the-badge)
![Evento](https://img.shields.io/badge/FMU_Tech_Inovação-2026.2-0D47A1?style=for-the-badge)

---

## 📋 Sobre o Projeto
O **Estoque Vital** é uma iniciativa desenvolvida no âmbito do desafio **FMU Tech Inovação (2026.2)**, alinhada ao **Objetivo de Desenvolvimento Sustentável 3 (ODS 3 — Saúde e Bem-Estar)** da Agenda 2030 da ONU. O projeto propõe uma solução analítica voltada à gestão inteligente da cadeia de suprimentos farmacêuticos no Sistema Único de Saúde (SUS).

---

## 1. 🎯 Descrição do Problema

### O Desafio
A gestão logística de medicamentos na rede pública brasileira enfrenta um paradoxo crítico: enquanto milhares de pacientes sofrem com o **desabastecimento de fármacos essenciais** nas Unidades Básicas de Saúde (UBSs), toneladas de medicamentos são descartadas anualmente nos almoxarifados públicos por **perda de prazo de validade** e falhas na distribuição entre unidades.

### Público e Contexto Afetado
* **Pacientes do SUS:** Especialmente idosos, gestantes e portadores de doenças crônicas (como hipertensão e diabetes) que dependem da retirada contínua de medicamentos gratuitos para manter seus tratamentos.
* **Gestores e Farmacêuticos Públicos:** Profissionais das Secretarias de Saúde e UBSs que operam frequentemente sem ferramentas preditivas para antecipar picos de demanda ou realocar lotes próximos ao vencimento.

### Bases de Dados Públicas Utilizadas
Para fundamentar o diagnóstico e alimentar o protótipo analítico, serão utilizadas bases de dados reais e abertas:
* **DATASUS / Ministério da Saúde:** Dados de produção ambulatorial, dispensação e indicadores epidemiológicos por região.
* **Portal da Transparência / Compras.gov.br:** Registros de licitações, aquisições e valores unitários de medicamentos essenciais (RENAME).
* **Portais de Dados Abertos Estaduais e Municipais (ex.: Prefeitura de São Paulo / SES-SP):** Boletins de estoque, listas de disponibilidade de medicamentos na rede básica e histórico de consumo regional.

---

## 2. 💻 Proposta de Solução Tecnológica

### Como a Solução Ataca o Problema
O **Estoque Vital** consiste em um **painel analítico interativo (Dashboard de Apoio à Decisão)** capaz de cruzar o histórico de dispensação (saída de medicamentos) com o saldo atual em estoque e as datas de validade dos lotes. A partir desse cruzamento, o sistema gera três frentes de ação:
1. **Alerta de Risco de Ruptura:** Identifica unidades onde o ritmo de consumo esgotará o estoque antes da próxima reposição prevista.
2. **Alerta de Risco de Desperdício (Validade):** Sinaliza lotes com baixa rotatividade e vencimento próximo (30, 60 e 90 dias), sugerindo o remanejamento entre UBSs próximas.
3. **Visão Consolidada por Região:** Permite ao gestor visualizar quais medicamentos da Relação Nacional de Medicamentos Essenciais (RENAME) apresentam maior criticidade.

### Stack Tecnológica
* **Linguagem de Programação:** `Python 3.11+`
* **Manipulação e Análise de Dados:** `Pandas` e `NumPy` (limpeza, tratamento de dados públicos, cruzamento de tabelas e cálculo de giro de estoque).
* **Visualização e Prototipagem Web:** `Streamlit` e `Plotly` (construção rápida de uma interface web interativa com gráficos dinâmicos e filtros por unidade/medicamento).
* **Armazenamento de Dados:** `SQLite` e arquivos estruturados em `.csv` / `.parquet` (banco de dados relacional leve para armazenar as bases tratadas e simular consultas reais).

### Justificativa das Escolhas Técnicas
Considerando o escopo de desenvolvimento do **2º semestre de Ciência de Dados**, o ecossistema **Python + Pandas + Streamlit** oferece o melhor equilíbrio entre rigor analítico e agilidade de entrega. Ele elimina a complexidade de configurar infraestruturas pesadas de front-end e back-end separados, permitindo que o grupo foque na qualidade do tratamento dos dados públicos, na lógica de detecção de gargalos e na clareza visual do protótipo funcional.

---

## 3. 🎨 Identidade Visual Inicial

### Conceito do Logotipo
O logotipo do **Estoque Vital** combina uma **cruz médica minimalista** (representando a assistência à saúde) integrada a **barras de crescimento/fluxo ascendente** e um indicador de verificação (simbolizando dados organizados, controle de estoque e eficiência logística).

*(Nota: Inserir aqui a imagem `logo.png` salva na pasta `/assets` do repositório)*

### Paleta de Cores
| Cor | Código Hex | Aplicação | Significado |
| :--- | :--- | :--- | :--- |
| **Azul Institucional** | `#1E88E5` | Cabeçalhos, botões principais e identidade primária | Confiança, seriedade, transparência e saúde pública |
| **Verde Sustentabilidade** | `#2E7D32` | Indicadores positivos, status "Estoque Seguro" e badges ODS 3 | Vida, bem-estar e combate ao desperdício |
| **Âmbar Alerta** | `#F9A825` | Alertas preventivos (lotes a vencer em 60-90 dias) | Atenção logística e prevenção de perdas |
| **Vermelho Crítico** | `#D32F2F` | Alertas urgentes (risco imediato de falta ou vencimento < 30 dias) | Criticidade e tomada de decisão imediata |
| **Cinza Gelo / Fundo** | `#F5F7FA` | Plano de fundo da aplicação e cartões de métricas | Clareza visual, limpeza e legibilidade |

### Tipografia
* **Títulos e Destaques:** `Inter` (SemiBold / Bold) — Moderna, geométrica e de alta legibilidade em telas.
* **Corpo de Texto e Tabelas de Dados:** `Roboto` (Regular / Medium) — Excelente leitura para números, indicadores e relatórios técnicos.

---

## 4. 🚀 Pitch Inicial
> *"Todos os anos, a saúde pública brasileira enfrenta uma contradição silenciosa: pacientes saem das Unidades Básicas de Saúde sem seus medicamentos essenciais, enquanto lotes inteiros vencem e são descartados nos almoxarifados por falta de visibilidade logística. O **Estoque Vital** nasce para resolver esse gargalo por meio da ciência de dados. Ao integrar bases públicas de consumo, distribuição e validade, nossa plataforma transforma planilhas estáticas em alertas preditivos inteligentes — permitindo que gestores antecipem faltas, remanejem estoques antes do vencimento e garantam que o recurso público chegue a quem mais precisa, na hora certa."*

---

## 5. 📂 Estrutura Planejada do Repositório
```text
estoque-vital/
├── assets/               # Logotipo, paleta de cores e recursos visuais
├── data/                 # Bases de dados públicas brutas e tratadas (CSV / SQLite)
├── notebooks/            # Exploração inicial e limpeza de dados (Jupyter/Colab)
├── src/                  # Código-fonte da aplicação e dashboard (Streamlit)
└── README.md             # Documentação oficial do projeto (Checkpoint 1)

## 👥 Equipe e Contribuições
Projeto desenvolvido pelos discentes do 2º semestre de **Ciência de Dados — Centro Universitário FMU**:

| Integrante | RA | Papel / Foco no Projeto | GitHub |
| :--- | :--- | :--- | :--- |
| **Seu Nome Completo** | `Seu RA` | Coleta e Tratamento de Dados (ETL) | [@Vinicius-prog-dev](https://github.com/Vinicius-prog-dev) |
| **Nome do Colega 2** | `RA do Colega 2` | Análise Exploratória e Regras de Alerta | [@usuario2](https://github.com/) |
| **Nome do Colega 3** | `RA do Colega 3` | Prototipagem do Dashboard (Streamlit) | [@usuario3](https://github.com/) |
| **Nome do Colega 4** | `RA do Colega 4` | Identidade Visual, Documentação e Pitch | [@usuario4](https://github.com/) |
