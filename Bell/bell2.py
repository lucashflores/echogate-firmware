import gpiozero

# Conecte o botão ao GPIO 2
button = gpiozero.Button(17)
i = 0
# Loop infinito
while True:
    if button.is_pressed:
        print(f"Campainha {i}")
        i += 1
    else:
        print("Nada")