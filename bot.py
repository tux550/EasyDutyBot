import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from secret import BOT_KEY
from datetime import datetime

# Logger Config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)



OPTIONS, RECIEVED_DATE, RECIEVED_TIME, RECIEVED_LOCATION, RECIEVED_EXTRA, RECIEVED_CONFIRMATION, RECIEVED_FAQ, RECIEVED_NUMBER = range(8)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [["Reserva", "Consulta"]]
    
    user = update.message.from_user
    logger.info(
        "START: User %s: %s %s", user.id, user.first_name, user.last_name
    )

    await update.message.reply_text(
        "¡Bienvenido a EasyDuty! Estoy aquí para ayudarte con tus reservas de servicios de limpieza o cualquier consulta que tengas.\n"
        "AVISO: Necesita tener un username registrado para un correcto funcionamiento de este bot.\n"
        "Enviar /cancelar para terminar la conversación.\n\n"
        "¿En qué puedo asistirte hoy?",

        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Seleccionar opcion"
        ),
    )
    return OPTIONS




async def reserva_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '¡Perfecto!\n'
        '¿Cual sera la fecha del servicio? (Formato dd/mm/yy)'
    )
    return RECIEVED_DATE

async def reserva_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    try:
        # Validate and Save Date
        datetime.strptime(text, "%d/%m/%y")
        context.user_data["date"] = text
    except:
        # Handle exception
        await update.message.reply_text(
            'Error: Ingrese una fecha con el formato dd/mm/yy\n'
            '(Ejemplo: 31/01/23)\n'
            '¿Cual sera la fecha del servicio?'
        )
        return RECIEVED_DATE
    # Ask time
    await update.message.reply_text(
        '¿A que hora iniciara el servicio? (Formato de 24 horas hh:mm )'
    )
    return RECIEVED_TIME

async def reserva_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    try:
        # Validate and Save Time
        datetime.strptime(text, "%H:%M")
        context.user_data["time"] = text
    except:
        # Handle exception
        await update.message.reply_text(
            'Error: Ingrese una hora con el formato de 24 horas hh:mm\n'
            '(Ejemplo: 13:00)\n'
            '¿A que hora iniciara el servicio?'
        )
        return RECIEVED_TIME
    # Ask location
    await update.message.reply_text(
        '¿Cual sera la locación en la que se realizar el servicio?'
    )
    return RECIEVED_LOCATION

async def reserva_extra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save Date
    text = update.message.text
    context.user_data["location"] = text
    # Ask location
    await update.message.reply_text(
        'Si tiene algun comentario adicional para el servicio escribalo a continaución:'
    )
    return RECIEVED_EXTRA
    

async def reserva_confirmacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save Location
    text = update.message.text
    context.user_data["extra"] = text
    # Ask confirmation
    user_data = context.user_data
    reply_keyboard = [["Si", "No"]]
    await update.message.reply_text(
        'Los datos de su reserva son:\n'
        f'Fecha:{user_data["date"]}\n'
        f'Hora:{user_data["time"]}\n'
        f'Locacion:{user_data["location"]}\n'
        f'Anotaciones:{user_data["extra"]}\n'
        '¿Confirma este servicio?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Confirmar"
        ),
    )
    return RECIEVED_CONFIRMATION

async def reserva_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text=="No":
        await update.message.reply_text(
            'Se cancelo el servicio.',
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    else:
        user_data = context.user_data
        user = update.message.from_user
        logger.info(
            "RESERVA: User %s: %s %s", user.id, user.first_name, user.last_name
        )
        with open("reservas.csv", "a") as file:
            file.write(f'{user.username};{user_data["date"]};{user_data["time"]};{user_data["location"]};{user_data["extra"]}\n')
        await update.message.reply_text(
            'El servicio a sido registrado, pronto recibira un mensaje confirmando su reserva.\n'
            '¡Muchas gracias por su preferencia!',
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END


async def consulta_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Escriba su consulta:'
    )
    return RECIEVED_FAQ


async def consulta_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    logger.info(
        "CONSULTA: User %s: %s %s", user.id, user.first_name, user.last_name
    )
    with open("consultas.csv", "a") as file:
        file.write(f'{user.username};{text}\n')
    await update.message.reply_text(
        'Se ha registrado su pregunta, pronto recibira un mensaje de uno de nuestros profesionales resolviendo su consulta.\n'
        '¡Muchas gracias por su interes!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END



async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_KEY).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            OPTIONS: [
                MessageHandler(
                    filters.Regex("^Reserva$"), reserva_date
                ), 
                MessageHandler(
                    filters.Regex("^Consulta$"), consulta_pregunta
                ), 
            ],
            RECIEVED_DATE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND), reserva_time
                )
            ],
            RECIEVED_TIME: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND), reserva_location
                )
            ],
            RECIEVED_LOCATION: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND), reserva_extra
                )
            ],
            RECIEVED_EXTRA: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND), reserva_confirmacion
                )
            ],
            RECIEVED_CONFIRMATION: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND), reserva_fin
                )
            ],
            RECIEVED_FAQ: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND),
                    consulta_fin,
                )
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()