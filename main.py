import base64
import os
import random

import requests
from vkbottle import PhotoMessageUploader
from vkbottle.bot import Bot, Message

from config import VK_GROUP_TOKEN, STEPS_GLOBAL, DIFFUSERS_API
from presets import PROMPT, RESOLUTIONS, NEGATIVE_PROMPT

style_presets = dict()
negative_prompt_presets = dict()
resolution_presets = dict()
seed_presets = dict()

bot = Bot(token=VK_GROUP_TOKEN)

photo_uploader = PhotoMessageUploader(bot.api)


@bot.on.message(text="/привет")
async def start_handler(message):
    await message.answer(message="Привет!")


def user_verification(user_id):
    if user_id not in style_presets:
        style_presets[user_id] = PROMPT['none']
    if user_id not in resolution_presets:
        resolution_presets[user_id] = RESOLUTIONS['1:1']
    if user_id not in negative_prompt_presets:
        negative_prompt_presets[user_id] = NEGATIVE_PROMPT['standard']
    if user_id not in seed_presets:
        seed_presets[user_id] = "random"


def get_seed(user_id):
    return random.randint(0, 1024) if seed_presets[user_id] == "random" else seed_presets[user_id]


async def get_images(users_info, message, response):
    images = []
    index = 0
    for element in response['images']:
        name = "users/{}_{}.png".format(users_info[0].id, index)
        with open(name, "wb") as f:
            f.write(base64.b64decode(element))
            images.append(await photo_uploader.upload(
                file_source=name,
                peer_id=message.peer_id,
            ))
        index = index + 1
    return images


def error_handler(response):
    decode_response = response.text
    if decode_response == '400':
        message_body = 'Ошибка 400. Bad Request.'
    elif decode_response == '404':
        message_body = 'Сервер недоступен. Повторите запрос позже.'
    elif decode_response == '500':
        message_body = 'Ошибка 500. Internal Server Error.'
    else:
        message_body = 'Произошла неизвестная ошибка. Повторите запрос позже.'
    return message_body


@bot.on.message(text=["/create <prompt>"])
@bot.on.message(text=["/создать <prompt>"])
async def text_to_image_handler(message: Message, prompt: str):
    command = "/text2img"

    users_info = await bot.api.users.get(message.from_id)
    user_id = users_info[0].id
    user_verification(user_id)

    notification = await message.answer("В процессе!")

    request_body = {
        "prompt": prompt + " " + style_presets[user_id],
        "negative_prompt": negative_prompt_presets[user_id],
        "scheduler": "EulerAncestralDiscreteScheduler",
        "image_height": resolution_presets[user_id]['height'],
        "image_width": resolution_presets[user_id]['width'],
        "num_images": 3,
        "guidance_scale": 7,
        "steps": STEPS_GLOBAL,
        "seed": get_seed(user_id)
    }

    response = requests.post(DIFFUSERS_API + command, json=request_body,
                             headers={"Content-Type": "application/json"})

    # Проверяем запрос на ошибки.
    if response.text != '200':
        await message.answer(message=error_handler(response))
        return

    images = await get_images(users_info, message, response.json())

    message_body = 'Prompt: {} \n\n' \
                   'Negative Prompt: {} \n\n' \
                   'Seed: {} \n\n' \
        .format(request_body['prompt'],
                request_body['negative_prompt'],
                request_body['seed'])

    await message.answer(message=message_body, attachment=images)


@bot.on.message(text=["/img <prompt>"])
async def image_to_image_handler(message: Message, prompt: str):
    command = "/img2img"

    users_info = await bot.api.users.get(message.from_id)
    user_id = users_info[0].id
    user_verification(user_id)

    # Парсим ссылку на изображение из сообщения.
    input_image = message.attachments[0].photo.sizes[3].url

    p = requests.get(input_image)
    out = open("users/input_img2img_{}.jpg".format(user_id), "wb")
    out.write(p.content)
    out.close()

    headers = {
        'accept': 'application/json',
    }

    params = {
        "prompt": prompt + " " + style_presets[user_id],
        "negative_prompt": negative_prompt_presets[user_id],
        'scheduler': 'EulerAncestralDiscreteScheduler',
        'strength': '0.6',
        'num_images': '1',
        'guidance_scale': '7',
        'steps': STEPS_GLOBAL,
        'seed': get_seed(user_id),
    }

    files = {
        'image': open("users/input_img2img_{}.jpg".format(user_id), 'rb'),
    }

    response = requests.post(DIFFUSERS_API + command, params=params,
                             headers=headers, files=files)

    # Проверяем запрос на ошибки.
    if response.text != '200':
        await message.answer(message=error_handler(response))
        return

    images = get_images(users_info, message, response.json())

    await message.answer(message="Готово!", attachment=images)


@bot.on.message(text=["/стиль"])
@bot.on.message(text=["/style"])
async def style_list(message: Message):
    message_body = str()
    for i in PROMPT:
        message_body = message_body + i + "\t-\t[" + PROMPT[i] + "]\n"
    await message.answer("Доступные стили:\n{}".format(message_body))


@bot.on.message(text=["/стиль <args>"])
@bot.on.message(text=["/style <args>"])
async def style_handler(message: Message, args: str):
    users_info = await bot.api.users.get(message.from_id)
    if args in PROMPT:
        style_presets[users_info[0].id] = PROMPT[args]
        await message.answer("Выбран стиль: [{}]".format(args))
        return
    await message.answer("Выбранный стиль не найден."
                         "Введите команду '/стиль' для"
                         "просмотра справки.")


@bot.on.message(text=["/разрешение"])
@bot.on.message(text=["/resolution"])
async def resolution_list(message: Message):
    message_body = str()
    for i in RESOLUTIONS:
        message_body = message_body + i + "\t-\t[" + str(RESOLUTIONS[i]['height']) + "x" + str(
            RESOLUTIONS[i]['width']) + "]\n "
    await message.answer("Доступные разрешения:\n\n{}".format(message_body))


@bot.on.message(text=["/разрешение <args>"])
@bot.on.message(text=["/resolution <args>"])
async def resolution_handler(message: Message, args: str):
    users_info = await bot.api.users.get(message.from_id)
    if args in RESOLUTIONS:
        resolution_presets[users_info[0].id] = RESOLUTIONS[args]
        await message.answer("Выбранное разрешение: [{}]".format(args))
        return
    await message.answer("Выбранное разрешение не найдено."
                         "Введите команду '/разрешение' для"
                         "просмотра справки.")


@bot.on.message(text=["/seed <args>"])
async def seed_handler(message: Message, args: str):
    users_info = await bot.api.users.get(message.from_id)
    try:
        seed_presets[users_info[0].id] = int(args)
        await message.answer("Seed = [{}]".format(seed_presets[users_info[0].id]))
    except:
        seed_presets[users_info[0].id] = "random"
        await message.answer("Seed = случайному числу.")


@bot.on.message(text=["/помощь"])
async def help_handler(message: Message):
    await message.answer("/создать <запрос> - для генерации картинки из текста\n"
                         "/img <запрос> - для генерации картинки из картинки\n"
                         "/стиль - для выбора стиля\n"
                         "/разрешение - для выбора разрешения\n"
                         "/seed - для выбора случайного числа")


@bot.on.message()
async def main(message):
    await message.answer("Я вас не понимаю.\n"
                         "Введите /помощь для вывода доступных команд команд.")


if __name__ == '__main__':
    if not os.path.exists('users'):
        os.mkdir('users')

    bot.run_forever()
