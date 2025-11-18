# tictactoe-bot
import asyncio
import random
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = "8354533730:AAEKuNnc_Zvx56Vta650QUG3cqFqYHtIedE"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

EMPTY = "⬜"
X = "❌"
O = "⭕"

def encode_board(board):
    # Превращаем доску в строку: "⬜❌⭕|⬜⬜⬜|⭕⬜❌"
    return "|".join("".join(row) for row in board)

def decode_board(s):
    # Восстанавливаем доску из строки
    rows = s.split("|")
    return [list(row) for row in rows]

def new_board():
    return [[EMPTY for _ in range(3)] for _ in range(3)]

def board_text(board):
    return "\n".join(" | ".join(row) for row in board)

def kb(board, level="medium"):
    buttons = []
    board_code = encode_board(board)
    for i in range(3):
        row = []
        for j in range(3):
            row.append(InlineKeyboardButton(
                text=board[i][j],
                callback_data=f"m_{i}_{j}_{level}_{board_code}"
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔄 Новая игра", callback_data="new")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != EMPTY: return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != EMPTY: return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != EMPTY: return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != EMPTY: return board[0][2]
    return None

# ========== УРОВНИ СЛОЖНОСТИ ==========
def bot_easy_move(board):
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == EMPTY]
    return random.choice(empty) if empty else None

def bot_medium_move(board):
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == EMPTY]
    for pos in [(1,1), (0,0), (0,2), (2,0), (2,2)]:
        if pos in empty:
            return pos
    return random.choice(empty) if empty else None

def bot_hard_move(board):
    def minimax(b, is_max):
        w = winner(b)
        if w == O: return 10
        if w == X: return -10
        if all(cell != EMPTY for row in b for cell in row): return 0
        if is_max:
            best = -1000
            for i in range(3):
                for j in range(3):
                    if b[i][j] == EMPTY:
                        b[i][j] = O
                        best = max(best, minimax(b, False))
                        b[i][j] = EMPTY
            return best
        else:
            best = 1000
            for i in range(3):
                for j in range(3):
                    if b[i][j] == EMPTY:
                        b[i][j] = X
                        best = min(best, minimax(b, True))
                        b[i][j] = EMPTY
            return best
    best_move = None
    best_val = -1000
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == EMPTY]
    for i, j in empty:
        board[i][j] = O
        move_val = minimax(board, False)
        board[i][j] = EMPTY
        if move_val > best_val:
            best_val = move_val
            best_move = (i, j)
    return best_move

# ========== ХЭНДЛЕРЫ ==========
@router.message(Command("start"))
async def start(msg: Message):
    buttons = [
        [InlineKeyboardButton(text="🟢 Лёгкий", callback_data="diff_easy")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="diff_medium")],
        [InlineKeyboardButton(text="🔴 Сложный", callback_data="diff_hard")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer("🎮 Выберите уровень сложности:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("diff_"))
async def choose_diff(c: CallbackQuery):
    await c.answer()
    level = c.data.split("_")[1]
    board = new_board()
    text = f"🎮 Крестики-нолики\nУровень: {'🟢 Лёгкий' if level=='easy' else '🟡 Средний' if level=='medium' else '🔴 Сложный'}\n\n{board_text(board)}\n\n✅ Ваш ход (❌)"
    await c.message.edit_text(text, reply_markup=kb(board, level))

@router.callback_query(lambda c: c.data == "new")
async def new_game(c: CallbackQuery):
    await c.answer()
    buttons = [
        [InlineKeyboardButton(text="🟢 Лёгкий", callback_data="diff_easy")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="diff_medium")],
        [InlineKeyboardButton(text="🔴 Сложный", callback_data="diff_hard")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("🎮 Выберите уровень сложности:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("m_"))
async def move(c: CallbackQuery):
    await c.answer()
    parts = c.data.split("_")
    i, j = int(parts[1]), int(parts[2])
    level = parts[3]
    board_code = "_".join(parts[4:])  # остаток — закодированная доска
    board = decode_board(board_code.replace("_", "|"))

    if board[i][j] != EMPTY:
        await c.message.answer("🟨 Клетка занята!", show_alert=False)
        return

    # Ход игрока
    board[i][j] = X
    w = winner(board)
    if w == X:
        await c.message.edit_text(f"🎉 Вы победили!\nУровень: {level}\n\n{board_text(board)}", reply_markup=kb([['']*3]*3))
        return
    if all(cell != EMPTY for row in board for cell in row):
        await c.message.edit_text(f"🤝 Ничья!\nУровень: {level}\n\n{board_text(board)}", reply_markup=kb([['']*3]*3))
        return

    # Ход бота
    await c.message.edit_text(f"🤖 Ход бота…\nУровень: {level}\n\n{board_text(board)}", reply_markup=kb(board, level))
    await asyncio.sleep(0.7)

    # Выбираем стратегию
    if level == "easy":
        bm = bot_easy_move(board)
    elif level == "hard":
        bm = bot_hard_move(board)
    else:
        bm = bot_medium_move(board)

    if bm:
        bi, bj = bm
        board[bi][bj] = O
        w = winner(board)
        if w == O:
            await c.message.edit_text(f"😢 Бот победил!\nУровень: {level}\n\n{board_text(board)}", reply_markup=kb([['']*3]*3))
            return
        if all(cell != EMPTY for row in board for cell in row):
            await c.message.edit_text(f"🤝 Ничья!\nУровень: {level}\n\n{board_text(board)}", reply_markup=kb([['']*3]*3))
            return

    # Обновляем доску
    text = f"🎮 Крестики-нолики\nУровень: {level}\n\n{board_text(board)}\n\n✅ Ваш ход (❌)"
    await c.message.edit_text(text, reply_markup=kb(board, level))

async def main():
    print("✅ Игра запущена — теперь с надёжным обновлением поля!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
