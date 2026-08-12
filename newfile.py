from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

TOKEN = "YOUR_TOKEN"

# ==================================================
# 五子棋设置
# ==================================================

SIZE = 19

games = {}


# ==================================================
# 原本的 Commands
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎来到有点缺爱的机器人，我想你来到这边100%是只有被骂的份"
    )


async def sb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "can u pls shut fucking up"
    )


async def ganasai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "sb"
    )


async def que_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "你是缺爱吗？"
    )


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("damn")


# ==================================================
# 创建棋盘
# ==================================================

def create_board():
    return [
        ["." for _ in range(SIZE)]
        for _ in range(SIZE)
    ]


# ==================================================
# 创建 Telegram 棋盘
# ==================================================

def make_keyboard(board):

    keyboard = []

    for r in range(SIZE):

        row = []

        for c in range(SIZE):

            if board[r][c] == "B":
                text = "⚫"

            elif board[r][c] == "W":
                text = "⚪"

            else:
                text = "·"

            row.append(
                InlineKeyboardButton(
                    text,
                    callback_data=f"move_{r}_{c}"
                )
            )

        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# 判断五连
# ==================================================

def check_win(board, row, col, player):

    directions = [
        (1, 0),
        (0, 1),
        (1, 1),
        (1, -1)
    ]

    for dr, dc in directions:

        count = 1

        # 正方向
        r = row + dr
        c = col + dc

        while (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == player
        ):

            count += 1

            r += dr
            c += dc

        # 反方向
        r = row - dr
        c = col - dc

        while (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == player
        ):

            count += 1

            r -= dr
            c -= dc

        if count >= 5:
            return True

    return False


# ==================================================
# 判断棋盘是否满
# ==================================================

def board_full(board):

    for row in board:

        if "." in row:
            return False

    return True


# ==================================================
# AI 评分
# ==================================================

def evaluate_position(board, row, col, player):

    score = 0

    directions = [
        (1, 0),
        (0, 1),
        (1, 1),
        (1, -1)
    ]

    for dr, dc in directions:

        count = 1
        open_ends = 0

        # 正方向
        r = row + dr
        c = col + dc

        while (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == player
        ):

            count += 1

            r += dr
            c += dc

        if (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == "."
        ):

            open_ends += 1

        # 反方向
        r = row - dr
        c = col - dc

        while (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == player
        ):

            count += 1

            r -= dr
            c -= dc

        if (
            0 <= r < SIZE
            and 0 <= c < SIZE
            and board[r][c] == "."
        ):

            open_ends += 1

        # 棋型评分

        if count >= 5:

            score += 100000

        elif count == 4:

            if open_ends == 2:
                score += 10000

            elif open_ends == 1:
                score += 5000

        elif count == 3:

            if open_ends == 2:
                score += 1000

            elif open_ends == 1:
                score += 300

        elif count == 2:

            if open_ends == 2:
                score += 100

            elif open_ends == 1:
                score += 30

    return score


# ==================================================
# 只寻找棋子附近的位置
# ==================================================

def get_candidates(board):

    candidates = set()

    for r in range(SIZE):

        for c in range(SIZE):

            if board[r][c] != ".":

                for dr in range(-2, 3):

                    for dc in range(-2, 3):

                        nr = r + dr
                        nc = c + dc

                        if (
                            0 <= nr < SIZE
                            and 0 <= nc < SIZE
                            and board[nr][nc] == "."
                        ):

                            candidates.add(
                                (nr, nc)
                            )

    # 第一手棋放中间
    if not candidates:

        center = SIZE // 2

        return [(center, center)]

    return list(candidates)


# ==================================================
# AI 下棋
# ==================================================

def bot_move(board):

    candidates = get_candidates(board)

    best_move = None
    best_score = -1

    for r, c in candidates:

        # ==========================================
        # AI 进攻
        # ==========================================

        board[r][c] = "W"

        attack_score = evaluate_position(
            board,
            r,
            c,
            "W"
        )

        # AI 可以直接获胜
        if check_win(
            board,
            r,
            c,
            "W"
        ):

            board[r][c] = "."

            return r, c

        board[r][c] = "."

        # ==========================================
        # AI 防守
        # ==========================================

        board[r][c] = "B"

        defense_score = evaluate_position(
            board,
            r,
            c,
            "B"
        )

        # 玩家如果下这里会赢
        if check_win(
            board,
            r,
            c,
            "B"
        ):

            board[r][c] = "W"

            return r, c

        board[r][c] = "."

        # ==========================================
        # 附近棋子奖励
        # ==========================================

        nearby_score = 0

        for dr in range(-2, 3):

            for dc in range(-2, 3):

                if dr == 0 and dc == 0:
                    continue

                nr = r + dr
                nc = c + dc

                if (
                    0 <= nr < SIZE
                    and 0 <= nc < SIZE
                ):

                    if board[nr][nc] == "W":

                        nearby_score += 12

                    elif board[nr][nc] == "B":

                        nearby_score += 10

        # ==========================================
        # 中央奖励
        # ==========================================

        center = SIZE // 2

        center_score = (
            20
            - abs(r - center)
            - abs(c - center)
        )

        # ==========================================
        # 最终评分
        # ==========================================

        total_score = (
            attack_score * 2
            + defense_score * 3
            + nearby_score
            + center_score
        )

        if total_score > best_score:

            best_score = total_score

            best_move = (r, c)

    return best_move


# ==================================================
# /gomoku
# ==================================================

async def gomoku(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    games[chat_id] = {
        "board": create_board(),
        "active": True
    }

    await update.message.reply_text(
        "🎮 五子棋开始！\n\n"
        "⚫ 你\n"
        "⚪ Bot\n\n"
        "19 × 19 棋盘\n"
        "点击棋盘下棋！",
        reply_markup=make_keyboard(
            games[chat_id]["board"]
        )
    )


# ==================================================
# /quit
# ==================================================

async def quit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id in games:

        del games[chat_id]

    await update.message.reply_text(
        "🚪 五子棋已退出。\n\n"
        "输入 /gomoku 可以重新开始。"
    )


# ==================================================
# 玩家点击棋盘
# ==================================================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat.id

    # 没有游戏
    if chat_id not in games:

        await query.answer(
            "没有正在进行的游戏，请输入 /gomoku",
            show_alert=True
        )

        return

    game = games[chat_id]

    if not game["active"]:
        return

    board = game["board"]

    # 获取按钮位置
    data = query.data

    if not data.startswith("move_"):
        return

    _, row, col = data.split("_")

    row = int(row)
    col = int(col)

    # 已经有棋子
    if board[row][col] != ".":

        await query.answer(
            "❌ 这里已经有棋子了！",
            show_alert=True
        )

        return

    # ==========================================
    # 玩家下棋
    # ==========================================

    board[row][col] = "B"

    # 玩家赢
    if check_win(
        board,
        row,
        col,
        "B"
    ):

        game["active"] = False

        await query.edit_message_text(
            "🎉 你赢了！\n\n"
            "⚫ 你已经五连！\n\n"
            "输入 /gomoku 再来一局。",
            reply_markup=make_keyboard(board)
        )

        return

    # 平局
    if board_full(board):

        game["active"] = False

        await query.edit_message_text(
            "🤝 平局！\n\n"
            "输入 /gomoku 再来一局。",
            reply_markup=make_keyboard(board)
        )

        return

    # ==========================================
    # AI 下棋
    # ==========================================

    result = bot_move(board)

    if result is None:

        game["active"] = False

        await query.edit_message_text(
            "🤝 平局！",
            reply_markup=make_keyboard(board)
        )

        return

    bot_row, bot_col = result

    board[bot_row][bot_col] = "W"

    # AI 赢
    if check_win(
        board,
        bot_row,
        bot_col,
        "W"
    ):

        game["active"] = False

        await query.edit_message_text(
            "😈 Bot 赢了！\n\n"
            "⚪ Bot 已经五连！\n\n"
            "输入 /gomoku 再挑战一次。",
            reply_markup=make_keyboard(board)
        )

        return

    # 平局
    if board_full(board):

        game["active"] = False

        await query.edit_message_text(
            "🤝 平局！\n\n"
            "输入 /gomoku 再来一局。",
            reply_markup=make_keyboard(board)
        )

        return

    # ==========================================
    # 更新棋盘
    # ==========================================

    await query.edit_message_text(
        "🎮 五子棋\n\n"
        "⚫ 你\n"
        "⚪ Bot\n\n"
        "轮到你了！",
        reply_markup=make_keyboard(board)
    )


# ==================================================
# 建立 Bot
# ==================================================

app = Application.builder().token(TOKEN).build()


# ==================================================
# Commands
# ==================================================

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("sb", sb)
)

app.add_handler(
    CommandHandler("ganasai", ganasai)
)

app.add_handler(
    CommandHandler("que_ai", que_ai)
)

app.add_handler(
    CommandHandler("gomoku", gomoku)
)

app.add_handler(
    CommandHandler("quit", quit_game)
)


# ==================================================
# 棋盘按钮
# ==================================================

app.add_handler(
    CallbackQueryHandler(button_click)
)


# ==================================================
# 普通文字 → damn
# ==================================================

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        fallback
    )
)


# ==================================================
# 启动
# ==================================================

print("Bot 已启动")

app.run_polling()
