import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
import asyncio
import random
import os
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB PARA O RENDER (MANTÉM O BOT ACORDADO) ---
app = Flask('')

@app.route('/')
def home():
    return "O bot do Hyzen RP está online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES ---
# O token agora é lido de forma segura pela variável de ambiente do Render (DISCORD_TOKEN)
TOKEN = os.getenv("MTU3MjcxMzE1Nzk3NjQwMDAxMg.GY47Xt.-NieyQs36vVf_mQ1-WO0Z8oy1k5Mz-PyxPOHSE")
ID_CARGO_ENTRADA = 1557488617407127604  # Cargo dado ao entrar
ID_CARGO_STAFF = 1557488577372364892    # Cargo de Staff com acesso aos comandos

# LINKS E IDS DAS CATEGORIAS DO DISCORD
URL_LOGO_THUMB = "https://media.discordapp.net/attachments/1572710527241560108/1572724177558044683/HyzenOficial.png?ex=6aff6907&is=6afe1787&hm=f79456ee61384a13d13220858216f2938c6d98ea69ba45431ec67ed08d246562&format=webp&quality=lossless&width=1024&height=1024"

CATEGORIAS_IDS = {
    "unban": 1557488752136560730,
    "streamer": 1557488742258712607,
    "org_cand": 1557488734134607962,
    "report_org": 1557488727536832512,
    "vip": 1557488726542782666,
    "bug": 1557488735862657184,
    "outros": 1557488743232045096,
    "report_player": 1557488749233971261
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- BOTÃO PARA FECHAR O TICKET ---
class FecharTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="fechar_ticket_btn")
    async def fechar_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 A encerrar e apagar este ticket em 5 segundos...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- FUNÇÃO AUXILIAR PARA CRIAR O CANAL ---
async def criar_ticket_com_formulario(interaction: discord.Interaction, tipo: str, dados: dict):
    guild = interaction.guild
    user = interaction.user
    nome_canal = f"ticket-{tipo}-{user.name.lower()}"

    canal_existente = discord.utils.get(guild.text_channels, name=nome_canal)
    if canal_existente:
        await interaction.response.send_message(f"❌ Já tens um ticket deste tipo aberto em {canal_existente.mention}!", ephemeral=True)
        return

    cat_id = CATEGORIAS_IDS.get(tipo)
    categoria = guild.get_channel(cat_id) if cat_id else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    canal_ticket = await guild.create_text_channel(name=nome_canal, category=categoria, overwrites=overwrites)
    await interaction.response.send_message(f"✅ Ticket criado com sucesso: {canal_ticket.mention}", ephemeral=True)

    nomes_tipos = {
        "unban": "Unbans", "report_player": "Report de Jogador", "vip": "VIPs",
        "org_cand": "Organizações", "outros": "Outros", "bug": "Report Bugs",
        "report_org": "Report Organização", "streamer": "Candidatura Streamers"
    }
    nome_amigavel = nomes_tipos.get(tipo, tipo.capitalize())

    embed = discord.Embed(
        description=(
            f"O teu ticket foi aberto com sucesso! A equipa de administração irá analisar o teu pedido e responder assim que possível.\n\n"
            f"🤍 **Enquanto aguardas:**\n\n"
            f"🔶 **Certifica-te de que forneceste todas as informações necessárias.**\n"
            f"🔶 **Evita enviar mensagens desnecessárias para não atrasar a resposta.**\n"
            f"🔶 **Mantém o respeito e aguarda pacientemente.**\n\n"
            f"⚠️ **Nota:** Devido a teres aberto ticket em **{nome_amigavel}**, a resposta pode demorar um pouco mais do que o habitual. Agradecemos pela tua paciência.\n\n"
            f"🔒 **O ticket será fechado pela Staff após a conclusão do processo.**"
        ),
        color=discord.Color.from_rgb(220, 20, 60)
    )

    embed.set_author(name="Hyzen RP | Suporte", icon_url=URL_LOGO_THUMB)
    embed.set_thumbnail(url=URL_LOGO_THUMB)
    
    for campo, valor in dados.items():
        embed.add_field(name=campo, value=valor if valor else "Não especificado", inline=False)

    embed.set_footer(text="Hyzen RP • Sistema de Tickets", icon_url=URL_LOGO_THUMB)
    
    await canal_ticket.send(content=f"{user.mention} Bem-vindo ao Suporte do Hyzen RP", embed=embed, view=FecharTicketView())

# --- MODALS (FORMULÁRIOS) ---
class ModalUnban(Modal, title="Unbans"):
    motivo_ban = TextInput(label="Porque foste banido?", placeholder="Explica o motivo do ban, se souberes.", style=discord.TextStyle.paragraph, required=True)
    rever = TextInput(label="Porque devemos rever?", placeholder="Diz-nos o teu lado da história.", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "unban", {"Porque foste banido?": self.motivo_ban.value, "Porque devemos rever?": self.rever.value})

class ModalReportPlayer(Modal, title="Report de Jogador"):
    discord_jogador = TextInput(label="Discord do jogador reportado", placeholder="Discord do jogador", required=True)
    aconteceu = TextInput(label="O que aconteceu?", placeholder="Explica a situação em detalhe.", style=discord.TextStyle.paragraph, required=True)
    provas = TextInput(label="Tens provas?", placeholder="Vídeo, prints, clip, testemunhas", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "report_player", {"Discord do Jogador": self.discord_jogador.value, "O que aconteceu?": self.aconteceu.value, "Provas": self.provas.value})

class ModalVip(Modal, title="VIPs"):
    assunto = TextInput(label="Assunto", placeholder="Explica o motivo de teres aberto o ticket.", required=True)
    detalhe = TextInput(label="Comprovativo / detalhe", placeholder="Explica o que pretendes.", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "vip", {"Assunto": self.assunto.value, "Detalhe": self.detalhe.value})

class ModalOrganizacoes(Modal, title="Organizações"):
    assunto = TextInput(label="Assunto", placeholder="Parceria, pedido, dúvida, etc.", required=True)
    detalhe = TextInput(label="Detalhes extra", placeholder="Escreve mais informação", style=discord.TextStyle.paragraph, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "org_cand", {"Assunto": self.assunto.value, "Detalhes Extra": self.detalhe.value})

class ModalOutros(Modal, title="Outros"):
    assunto = TextInput(label="Qual é o assunto?", placeholder="Escreve o teu problema ou dúvida.", required=True)
    detalhe = TextInput(label="Detalhes", placeholder="Explica com o máximo de detalhe", style=discord.TextStyle.paragraph, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "outros", {"Assunto": self.assunto.value, "Detalhes": self.detalhe.value})

class ModalBug(Modal, title="Report Bugs"):
    bug = TextInput(label="Qual é o bug?", placeholder="Descreve o bug com detalhe.", style=discord.TextStyle.paragraph, required=True)
    como = TextInput(label="Como aconteceu?", placeholder="Passos para reproduzir o bug.", style=discord.TextStyle.paragraph, required=True)
    provas = TextInput(label="Provas", placeholder="Prints, vídeo ou outra informação", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "bug", {"Qual é o bug?": self.bug.value, "Como aconteceu?": self.como.value, "Provas": self.provas.value})

class ModalReportOrg(Modal, title="Report Organização"):
    org = TextInput(label="Qual é a organização?", placeholder="Diz a organização que queres reportar.", required=True)
    aconteceu = TextInput(label="O Que aconteceu?", placeholder="Explica o sucedido.", style=discord.TextStyle.paragraph, required=True)
    provas = TextInput(label="Provas", placeholder="Prints, vídeo ou outra informação", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "report_org", {"Organização": self.org.value, "O que aconteceu?": self.aconteceu.value, "Provas": self.provas.value})

class ModalStreamer(Modal, title="Candidatura Streamers"):
    link = TextInput(label="Link Stream", placeholder="Mete aqui link da tua stream.", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket_com_formulario(interaction, "streamer", {"Link da Stream": self.link.value})

# --- MENU DE SELEÇÃO (DROPDOWN) ---
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Unbans", description="Pedidos de desbanimento", emoji="⛔", value="unban"),
            discord.SelectOption(label="Report de Jogador", description="Denunciar um jogador por quebra de regras", emoji="🚓", value="report_player"),
            discord.SelectOption(label="VIPs", description="Adquirir ou gerir vantagens VIP", emoji="💎", value="vip"),
            discord.SelectOption(label="Organizações", description="Assuntos e candidaturas de organizações", emoji="🗂️", value="org_cand"),
            discord.SelectOption(label="Outros", description="Dúvidas e questões gerais", emoji="🌐", value="outros"),
            discord.SelectOption(label="Report Bugs", description="Reportar erros e falhas no servidor", emoji="⚙️", value="bug"),
            discord.SelectOption(label="Report Organização", description="Denunciar uma facção ou organização", emoji="🔫", value="report_org"),
            discord.SelectOption(label="Candidatura Streamers", description="Parcerias e candidaturas de stream", emoji="📸", value="streamer"),
        ]
        super().__init__(placeholder="📂 Seleciona o departamento pretendido...", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        escolha = self.values[0]
        modals = {
            "unban": ModalUnban, "report_player": ModalReportPlayer, "vip": ModalVip,
            "org_cand": ModalOrganizacoes, "outros": ModalOutros, "bug": ModalBug,
            "report_org": ModalReportOrg, "streamer": ModalStreamer
        }
        if escolha in modals:
            await interaction.response.send_modal(modals[escolha]())

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# --- EVENTOS ---
@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(FecharTicketView())
    print(f"Bot Hyzen RP conectado com sucesso como: {bot.user.name}")

@bot.event
async def on_member_join(member):
    cargo = member.guild.get_role(ID_CARGO_ENTRADA)
    if cargo:
        try:
            await member.add_roles(cargo)
        except discord.Forbidden:
            print("Erro: O bot não tem permissões para atribuir o cargo.")

# --- COMANDOS ADMINISTRATIVOS PARA A STAFF ---

@bot.command(name="renomear", aliases=["ticketname"])
async def renomear(ctx, *, novo_nome: str):
    if not any(role.id == ID_CARGO_STAFF for role in ctx.author.roles):
        await ctx.send("❌ Não tens permissão para usar este comando!", delete_after=5)
        return
        
    if not novo_nome.startswith("ticket-"):
        novo_nome = f"ticket-{novo_nome}"
        
    await ctx.channel.edit(name=novo_nome)
    await ctx.send(f"✅ Canal renomeado com sucesso para: **{novo_nome}**")

@bot.command(name="adicionar", aliases=["add"])
async def adicionar(ctx, membro: discord.Member):
    if not any(role.id == ID_CARGO_STAFF for role in ctx.author.roles):
        await ctx.send("❌ Não tens permissão para usar este comando!", delete_after=5)
        return
    await ctx.channel.set_permissions(membro, read_messages=True, send_messages=True, attach_files=True)
    await ctx.send(f"✅ {membro.mention} foi adicionado a este ticket.")

@bot.command(name="remover", aliases=["remove"])
async def remover(ctx, membro: discord.Member):
    if not any(role.id == ID_CARGO_STAFF for role in ctx.author.roles):
        await ctx.send("❌ Não tens permissão para usar este comando!", delete_after=5)
        return
    await ctx.channel.set_permissions(membro, overwrite=None)
    await ctx.send(f"❌ {membro.mention} foi removido deste ticket.")

@bot.command(name="mover")
async def mover(ctx, categoria_tipo: str):
    if not any(role.id == ID_CARGO_STAFF for role in ctx.author.roles):
        await ctx.send("❌ Não tens permissão para usar este comando!", delete_after=5)
        return
        
    categoria_tipo = categoria_tipo.lower()
    cat_id = CATEGORIAS_IDS.get(categoria_tipo)
    
    if not cat_id:
        categorias_disponiveis = ", ".join(CATEGORIAS_IDS.keys())
        await ctx.send(f"❌ Categoria inválida! Escolhe uma destas: `{categorias_disponiveis}`")
        return

    categoria = ctx.guild.get_channel(cat_id)
    if categoria:
        await ctx.channel.edit(category=categoria)
        await ctx.send(f"📁 Ticket movido com sucesso para a categoria **{categoria.name}**!")
    else:
        await ctx.send("❌ A categoria configurada não foi encontrada no servidor.")

@bot.command(name="votacao")
@commands.has_permissions(administrator=True)
async def votacao(ctx, *, motivo: str):
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="📊 NOVA VOTAÇÃO — HYZEN RP",
        description=f"**{motivo}**\n\nReage abaixo para votar:\n✅ — **Sim**\n❌ — **Não**",
        color=discord.Color.from_rgb(220, 20, 60)
    )
    embed.set_thumbnail(url=URL_LOGO_THUMB)
    embed.set_footer(text=f"Votação iniciada por {ctx.author.display_name} • Hyzen RP", icon_url=URL_LOGO_THUMB)

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.command(name="giveaway", aliases=["sorteio"])
@commands.has_permissions(administrator=True)
async def giveaway(ctx, tempo: str, *, premio: str):
    try:
        await ctx.message.delete()
    except:
        pass

    tempo_unidade = tempo[-1].lower()
    try:
        tempo_valor = int(tempo[:-1])
    except ValueError:
        await ctx.send("❌ Formato de tempo inválido! Usa por exemplo: `10s`, `5m` ou `2h`.", delete_after=5)
        return

    segundos = 0
    if tempo_unidade == 's':
        segundos = tempo_valor
    elif tempo_unidade == 'm':
        segundos = tempo_valor * 60
    elif tempo_unidade == 'h':
        segundos = tempo_valor * 3600
    else:
        await ctx.send("❌ Usa **s** para segundos, **m** para minutos ou **h** para horas (ex: `30s`, `5m`).", delete_after=5)
        return

    embed = discord.Embed(
        title="🎉 NOVO GIVEAWAY — HYZEN RP",
        description=(
            f"Prémio: **{premio}**\n\n"
            f"⏱️ Duração: **{tempo}**\n"
            f"👤 Host: {ctx.author.mention}\n\n"
            f"Clica na reação 🎉 para participar!"
        ),
        color=discord.Color.from_rgb(220, 20, 60)
    )
    embed.set_thumbnail(url=URL_LOGO_THUMB)
    embed.set_footer(text="Hyzen RP • Sorteios oficiais", icon_url=URL_LOGO_THUMB)

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

    await asyncio.sleep(segundos)

    try:
        msg = await ctx.channel.fetch_message(msg.id)
    except discord.NotFound:
        return

    utilizadores = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    utilizadores.append(user)

    if len(utilizadores) > 0:
        vencedor = random.choice(utilizadores)
        
        embed_fim = discord.Embed(
            title="🎉 GIVEAWAY TERMINADO 🎉",
            description=(
                f"Prémio: **{premio}**\n\n"
                f"🏆 Vencedor: {vencedor.mention} (`{vencedor}`)\n"
                f"Parabéns! Abre ticket para reclamar o teu prémio."
            ),
            color=discord.Color.green()
        )
        embed_fim.set_thumbnail(url=URL_LOGO_THUMB)
        embed_fim.set_footer(text="Hyzen RP • Giveaway Encerrado", icon_url=URL_LOGO_THUMB)
        
        await msg.edit(embed=embed_fim)
        await ctx.send(f"🎊 Parabéns {vencedor.mention}! Ganhaste **{premio}**!")
    else:
        embed_sem_participantes = discord.Embed(
            title="🎉 GIVEAWAY TERMINADO 🎉",
            description=f"Prémio: **{premio}**\n\n❌ Não houve participantes suficientes para realizar o sorteio.",
            color=discord.Color.red()
        )
        embed_sem_participantes.set_thumbnail(url=URL_LOGO_THUMB)
        await msg.edit(embed=embed_sem_participantes)
        await ctx.send("❌ O giveaway terminou, mas ninguém participou.")

# --- COMANDO DE SUGESTÕES (PARA TODOS) ---
@bot.command(name="sugestao", aliases=["sugestões", "suggestion"])
async def sugestao(ctx, *, ideia: str):
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="💡 NOVA SUGESTÃO — HYZEN RP",
        description=f"**Sugestão de {ctx.author.mention}:**\n\n> {ideia}",
        color=discord.Color.from_rgb(220, 20, 60)
    )
    embed.set_thumbnail(url=URL_LOGO_THUMB)
    embed.set_footer(text=f"ID do Autor: {ctx.author.id} • Hyzen RP", icon_url=URL_LOGO_THUMB)

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

# --- COMANDOS GERAIS (PAINEL MELHORADO) ---
@bot.command(name="painel")
@commands.has_permissions(administrator=True)
async def painel(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="⚡ HYZEN RP — CENTRAL DE ATENDIMENTO",
        description=(
            "Bem-vindo ao suporte oficial do **Hyzen RP**.\n"
            "Seleciona o departamento correto no menu abaixo para abrir um ticket privado com a nossa equipa.\n\n"
            "> ⚠️ **Aviso:** *Abre apenas um ticket de cada vez. O abuso deste sistema resultará em punições.*"
        ),
        color=discord.Color.from_rgb(220, 20, 60)
    )

    embed.add_field(
        name="🛡️ Moderação & Suporte",
        value=(
            "⛔ **Unbans** ➔ Pedidos de desbanimento\n"
            "🚓 **Report de Jogador** ➔ Denunciar quebras de regras\n"
            "🌐 **Outros** ➔ Dúvidas e questões gerais"
        ),
        inline=False
    )

    embed.add_field(
        name="💼 Facções, Empresas & Loja",
        value=(
            "💎 **VIPs** ➔ Aquisição e vantagens VIP\n"
            "🗂️ **Organizações** ➔ Assuntos e candidaturas de orgs\n"
            "🔫 **Report Organização** ➔ Denúncias a facções"
        ),
        inline=False
    )

    embed.add_field(
        name="🚀 Técnico & Criadores",
        value=(
            "⚙️ **Report Bugs** ➔ Erros e falhas do servidor\n"
            "📸 **Candidatura Streamers** ➔ Parcerias de stream"
        ),
        inline=False
    )
    
    embed.set_thumbnail(url=URL_LOGO_THUMB)
    embed.set_footer(text="Hyzen RP • Todos os direitos reservados", icon_url=URL_LOGO_THUMB)
    
    await ctx.send(embed=embed, view=TicketView())

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 {round(bot.latency * 1000)}ms")

# --- ARRANCAR O SERVIDOR WEB E O BOT ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
