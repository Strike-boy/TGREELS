@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(texts['help'][lang])

@dp.message_handler(commands=['about'])
async def about_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(texts['about'][lang])

@dp.message_handler(commands=['languages'])
async def languages_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch")
    await message.answer(texts['choose_lang'][lang], reply_markup=keyboard)

@dp.message_handler(commands=['stats'])
async def stats_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    count = get_downloads(message.from_user.id)
    await message.answer(f"{texts['stats'][lang]} {count}")

@dp.message_handler(lambda m: m.text in ["🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch"])
async def change_lang(message: types.Message):
    lang_code = {'🇷🇺 Русский': 'ru', '🇺🇸 English': 'en', '🇺🇦 Українська': 'ua', '🇩🇪 Deutsch': 'de'}[message.text]
    set_user_language(message.from_user.id, lang_code)
    await message.answer("✅ Язык обновлен!", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler()
async def download_video(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    await message.answer(texts['downloading'][lang])
    try:
        ydl_opts = {'outtmpl': 'video.%(ext)s', 'cookiefile': 'cookies.txt'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        with open('video.mp4', 'rb') as video:
            await message.answer_video(video)
        os.remove('video.mp4')
        increment_downloads(user_id)
    except Exception as e:
        await message.answer(f"{texts['error'][lang]} {e}")

def start_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

if name == "main":
    t = Thread(target=start_bot)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
