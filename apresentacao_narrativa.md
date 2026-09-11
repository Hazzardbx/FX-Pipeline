# Guião da apresentação — narrativa própria (rascunho, continuar)

> Isto NÃO é o `apresentacao_keypoints.md` (esse é "porquês" para responder a perguntas do Joseph).
> Isto é a ORDEM em que vou CONTAR a história do projeto — a forma como penso nisto naturalmente,
> capturada em 09/09/26 a partir de como expliquei o `main.py` ao Claude sem preparação nenhuma.
> Estado: cobre Extract→Transform→Load→Orchestrate. Falta continuar com Serve (views, Streamlit, deploy).
>
> **CORREÇÃO IMPORTANTE (10/09/26, feedback direto do Joseph em breakout room):** a estrutura de apresentação de sábado NÃO é narrar o pipeline main.py passo a passo (isso come os 10 minutos todos). Joseph foi explícito: **10 minutos, sem entrar em código**, estrutura de 4 perguntas: *what's the challenge — what I set out to accomplish — how did I do it — what's the result*. A narrativa detalhada do ETL abaixo (Partes 1-3) fica como material de apoio para perguntas do público/Joseph, NÃO como o guião principal dos 10 minutos. O guião principal ainda está por escrever, seguindo as 4 perguntas do Joseph.
>
> Feedback adicional do Joseph (10/09): confirmou que a maior parte do projeto podia ter sido feito em ~60-70 linhas de Python simples (sem Docker/Postgres/scheduler dedicado) — avaliação tecnicamente correta, mas Joseph validou a escolha de usar a stack completa dado o objetivo de Data Engineering ("está bom, só falta terminar o Streamlit"). Sugestão dele: adicionar gráficos no Streamlit, um por pergunta de negócio (`st.bar_chart` para pct_change/volatility, `st.line_chart` para trend).
>
> **RECEITA para o resto deste ficheiro (método, não conteúdo fixo):** ainda não se sabe ao certo tudo o que vai estar na app até ao dia. Sempre que uma parte nova ficar pronta (views, Streamlit, deploy), pedir ao Kalil para explicar essa parte por palavras próprias primeiro — sem preparação, tal como fez para o main.py. Capturar essa explicação quase verbatim aqui, na ordem em que ele a disse. É essa ordem/linguagem que se torna o esqueleto do guião, porque é a forma como ele pensa e se identifica com isso — não reescrever para soar mais "apresentação".
>
> **Sobre o idioma:** a apresentação vai ser em inglês (Kalil safa-se bem). Este ficheiro fica em português enquanto é rascunho de trabalho — só traduzir para inglês no fim, quando o guião estiver completo e fechado, não a cada secção nova.

---

## Parte 1 — main.py (Extract → Transform → Load), na minha própria ordem

Tudo começa com o `main.py`, que foi o que comecei a fazer no início do projeto:

1. Extraio dados da API.
2. `for` loop verifica se há erro e faz o request outra vez passado x tempo se tiver erro; se não tiver, continua.
3. Crio uma lista vazia.
4. Preencho a lista com um `for` loop vindo dos dados da API.
5. Crio um DataFrame com os dados.
6. Converto a coluna de data para `datetime`.
7. Verifico nulls e removo-os.
8. Crio uma query SQL para criar uma tabela com os dados extraídos.
9. Tento ligar à base de dados.
10. Tento inserir os dados na base de dados, vendo se o que estou a inserir já existe — não insere se já existir igual (upsert).
11. Fecho a ligação com a BD.

## Parte 2 — Orchestrate, a seguir no mesmo ficheiro

Depois disto, no `main.py`, entra o scheduler: depois de correr o "ir buscar dados na API e meter numa DataFrame", cria-se um job para fazer isto **on a schedule** (repetir sozinho, sem ação manual).

## Parte 3 — o gatilho real (clarificado em sessão, 09/09/26)

Pergunta que fiz e vale a pena manter no guião, porque é a pergunta natural que alguém no público também vai ter:
**"o que desencadeia tudo isto — é abrir o Docker, é clicar nalgum lado?"**

Resposta a usar na apresentação:
- Docker Desktop aberto sozinho não faz nada — é só o motor disponível.
- O gatilho real é o comando `docker compose up`.
- Isso arranca o container `app`, que corre automaticamente o `CMD ["python", "main.py"]` do `Dockerfile`.
- O `main.py` corre de cima a baixo, chama `run_pipeline()` (Extract→Transform→Load), depois `run_daily()` (arranca o scheduler e fica à espera).
- A partir daí, **não preciso de fazer mais nada** — o scheduler chama `run_pipeline()` sozinho, todos os dias úteis às 17h.

---

## Parte 4 — Serve (por escrever, continuar aqui à medida que fica pronto)

- [ ] Como as views (`pct_change_view`, etc.) se encaixam na história — provavelmente: "depois dos dados estarem na BD, preciso de uma forma de os mostrar sem misturar lógica SQL complexa dentro do Python"
- [ ] Como o Streamlit liga a tudo isto — "app separada, só lê, nunca escreve, nunca sabe que o main.py existe"
- [ ] Deploy no Streamlit Community Cloud — por fazer

**Lembrete para a próxima sessão de Serve:** continuar este ficheiro pedindo ao Kalil para explicar essa parte com as próprias palavras primeiro (mesmo padrão de hoje), não escrever isto por ele.

---

## Parte 5 — Guião real dos 10 minutos de sábado (por escrever)

Estrutura obrigatória (Joseph, 10/09/26): **Challenge → What I set out to accomplish → How I did it → Result.** Sem código. Alto nível.

- [ ] Challenge — por escrever
- [ ] What I set out to accomplish — por escrever
- [ ] How I did it — por escrever (versão resumida, não a Parte 1-3 inteira)
- [ ] Result — por escrever (inclui gráficos no Streamlit, deploy se concluído)
