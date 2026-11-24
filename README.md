# Gerenciador de Chamados de Suporte

Aplicação escolar para demonstrar a integração entre banco relacional (SQLite) e banco documental (MongoDB).

## Tecnologias
- Python e Flask: lógica da aplicação e rotas.
- SQLite: usuários, categorias e dados principais dos chamados.
- MongoDB: histórico de atendimento em documentos.
- HTML/CSS: interface.
- Git/GitHub: versionamento do código.

## Requisitos
- Python 3.10 ou superior.
- Conta/cluster MongoDB Atlas (ou MongoDB local).
- Git (para versionamento).

## Como executar

1. Baixe ou clone o repositório:
   ```bash
   git clone URL_DO_SEU_REPOSITORIO
   cd gerenciador_chamados
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   ```
   Windows:
   ```bash
   .venv\Scripts\activate
   ```
   Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure o MongoDB:
   - Crie um cluster gratuito no MongoDB Atlas.
   - Crie um usuário de banco e autorize o endereço IP usado na conexão.
   - Copie a URI de conexão.
   - Copie `.env.example` para um arquivo chamado `.env`.
   - Preencha `MONGO_URI` com sua URI real e altere `SECRET_KEY`.
   - O projeto carrega esse arquivo automaticamente. Não compartilhe o `.env` nem publique sua senha no GitHub.

5. Execute:
   ```bash
   python app.py
   ```
   Abra `http://127.0.0.1:5000` no navegador.

## Como funciona a integração
- SQLite guarda usuários, categorias e chamados, com chaves primárias e estrangeiras.
- MongoDB guarda cada evento do histórico como um documento com `chamado_id`, `data`, `responsavel`, `acao` e `observacoes`.
- Ao criar um chamado, o sistema tenta registrar o evento "Chamado criado" no MongoDB.
- Ao atualizar o status ou adicionar comentário, o sistema tenta gravar uma nova movimentação no MongoDB.
- A tela de detalhes consulta os documentos do histórico pelo `chamado_id`.

**Importante:** sem `MONGO_URI` válida, o sistema ainda permite testar o cadastro no SQLite, mas o histórico NoSQL não estará ativo. Para a demonstração completa exigida na atividade, configure o MongoDB.

## Estrutura
```text
gerenciador_chamados/
├── app.py
├── schema.sql
├── exemplo_historico.json
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── templates/
    ├── base.html
    ├── index.html
    ├── novo.html
    └── detalhe.html
```

## Sugestão de commits
Faça commits pequenos durante o desenvolvimento, por exemplo:
1. `chore: criar estrutura inicial do projeto`
2. `feat: criar tabelas relacionais no SQLite`
3. `feat: implementar cadastro e listagem de chamados`
4. `feat: integrar histórico com MongoDB`
5. `feat: criar interface de detalhes e atualização`
6. `docs: adicionar README e instruções`

## Questões para reflexão

**1. Por que os dados principais dos chamados foram armazenados em um banco SQL?**  
Porque são informações estruturadas e possuem relacionamentos. O SQL permite organizar os dados em tabelas, usar chaves primárias e estrangeiras e manter a integridade das informações.

**2. Por que o histórico de atendimento foi armazenado em um banco NoSQL?**  
Porque o histórico pode receber diferentes tipos de movimentações e observações ao longo do tempo. O MongoDB armazena essas informações em documentos flexíveis, facilitando a inclusão de novos detalhes.

**3. Quais são as principais diferenças entre os modelos relacional e documental?**  
O modelo relacional organiza os dados em tabelas com linhas, colunas e relacionamentos. O modelo documental armazena dados em documentos, geralmente no formato JSON/BSON, permitindo estruturas mais flexíveis.

**4. Qual é a importância do Git e do histórico de commits no desenvolvimento de software?**  
O Git registra as alterações feitas no código, permite voltar a versões anteriores e facilita o trabalho em equipe. Os commits mostram o que foi alterado em cada etapa do projeto.

## Observação para apresentação
Mostre o cadastro de um chamado, abra seus detalhes, altere o status e confira se a movimentação apareceu no histórico. Para comprovar o uso dos dois bancos, mostre o chamado no SQLite e o documento correspondente na coleção `historicos` do MongoDB.
