import azure.functions as func
import logging
import requests
import os
import pyodbc

app = func.FunctionApp()

# ---------------------------------------------------------
# 1. HTTP Trigger - Recebe parâmetro via URL (GET) e imprime na tela
# ---------------------------------------------------------
@app.route(route="greet", auth_level=func.AuthLevel.ANONYMOUS)
def greet(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processando requisição.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None

        if req_body:
            name = req_body.get('name')

    if name:
        mensagem = f"Olá, {name}! Parâmetro recebido com sucesso na função HTTP."
        logging.info(f"Parâmetro HTTP recebido: {name}")
        return func.HttpResponse(mensagem, status_code=200)
    else:
        return func.HttpResponse(
            "Por favor, passe o parâmetro 'name' na string de consulta (ex: ?name=SeuNome).",
            status_code=400
        )


# ---------------------------------------------------------
# 2. Timer Trigger (Simples) - Imprime apenas um log no terminal
# ---------------------------------------------------------
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=False,
                    use_monitor=False) 
def timer_log(mytimer: func.TimerRequest) -> None:
    if mytimer.past_due:
        logging.info('O timer está atrasado!')
    
    logging.info('Timer Trigger executado: Imprimindo apenas um log no terminal.')


# ---------------------------------------------------------
# 3. Timer Trigger (Chamada HTTP) - Faz chamada HTTP para a outra função
# ---------------------------------------------------------
@app.timer_trigger(schedule="0 */10 * * * *", arg_name="mycointimer", run_on_startup=False,
                    use_monitor=False)
def timer_call_http(mycointimer: func.TimerRequest) -> None:
    if mycointimer.past_due:
        logging.info('O timer está atrasado!')

    target_url = "https://funapp-themkemeier-g8dfdadsckdegjcb.canadacentral-01.azurewebsites.net/api/greet?name=ChamadaAutomaticaDoTimer"
    
    try:
        response = requests.get(target_url)
        logging.info(f"Timer chamando outra Function. Status: {response.status_code} | Resposta: {response.text}")
    except Exception as e:
        logging.error(f"Erro ao realizar a chamada HTTP pelo Timer: {e}")


# ---------------------------------------------------------
# 4. Timer Trigger - Conecta ao banco de dados e captura os dados de TODAS as tabelas
# ---------------------------------------------------------
@app.timer_trigger(schedule="0 */15 * * * *", arg_name="dbtimer", run_on_startup=False, use_monitor=False)
def capturar_todas_tabelas(dbtimer: func.TimerRequest) -> None:
    if dbtimer.past_due:
        logging.info('O timer do banco está atrasado!')

    logging.info('Iniciando captura de dados de todas as tabelas do ITSM...')

    # Recuperando credenciais com segurança via variáveis de ambiente
    db_server = os.environ.get("DB_SERVER")
    db_database = os.environ.get("DB_DATABASE")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")

    if not all([db_server, db_database, db_user, db_password]):
        logging.error("Erro: As variáveis de ambiente do banco de dados não estão configuradas.")
        return

    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={db_server};"
        f"DATABASE={db_database};"
        f"UID={db_user};"
        f"PWD={db_password}"
    )

    # Lista com as tabelas principais e essenciais do sistema
    tabelas = [
        "analista",
        "categoria",
        "chamado",
        "solicitante"
    ]
    try:
        logging.info(f"Conectando ao banco {db_database}...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        for tabela in tabelas:
            try:
                query = f"SELECT * FROM {tabela}"
                cursor.execute(query)
                registros = cursor.fetchall()
                logging.info(f"Sucesso: {len(registros)} registos capturados da tabela '{tabela}'.")
            except Exception as err_tabela:
                logging.error(f"Erro ao consultar a tabela '{tabela}': {str(err_tabela)}")

    except Exception as e:
        logging.error(f"Erro geral ao conectar ou consultar o banco de dados: {str(e)}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
            logging.info("Conexão com o banco de dados encerrada.")