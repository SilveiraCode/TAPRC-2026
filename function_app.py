import azure.functions as func
import logging
import requests

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

    # URL local apontando para a função HTTP criada acima com um texto identificador
    target_url = "https://funapp-themkemeier-g8dfdadsckdegjcb.canadacentral-01.azurewebsites.net/api/greet?name=ChamadaAutomaticaDoTimer"
    
    try:
        response = requests.get(target_url)
        logging.info(f"Timer chamando outra Function. Status: {response.status_code} | Resposta: {response.text}")
    except Exception as e:
        logging.error(f"Erro ao realizar a chamada HTTP pelo Timer: {e}")