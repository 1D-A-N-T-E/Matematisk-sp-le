import pygame
import pytmx
import pyscroll
import random

pygame.init()

screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Matemātikas spēle")
heart_img = pygame.image.load('images/Heart.png').convert_alpha()
clock = pygame.time.Clock()
FPS = 60


# ---------------------------------------------------
# PLAYER CLASS
# ---------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # Animācijas
        self.walk_right = [
            pygame.image.load('images/Right_1.png').convert_alpha(),
            pygame.image.load('images/Right_2.png').convert_alpha(),
            pygame.image.load('images/Right_3.png').convert_alpha()
        ]
        self.walk_left = [
            pygame.image.load('images/left_1.png').convert_alpha(),
            pygame.image.load('images/left_2.png').convert_alpha(),
            pygame.image.load('images/left_3.png').convert_alpha()
        ]
        self.walk_front = [
            pygame.image.load('images/front1.png').convert_alpha(),
            pygame.image.load('images/front2.png').convert_alpha(),
            pygame.image.load('images/front3.png').convert_alpha()
        ]
        self.walk_back = [
            pygame.image.load('images/back1.png').convert_alpha(),
            pygame.image.load('images/back2.png').convert_alpha(),
            pygame.image.load('images/back3.png').convert_alpha()
        ]

        self.image = self.walk_right[0]
        self.rect = self.image.get_rect(center=(x, y)) #Uztaisīt taisnstūri precīzi tik lielu, cik ir bilde, un novietot to pasaulē.

        self.speed = 3
        self.anim_index = 0
        self.dir = "right"

    def update(self, collision_rects):
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            dx = -self.speed
            self.dir = "left"
        if keys[pygame.K_d]:
            dx = self.speed
            self.dir = "right"
        if keys[pygame.K_w]:
            dy = -self.speed
            self.dir = "front"
        if keys[pygame.K_s]:
            dy = self.speed
            self.dir = "back"

        # Animācija
        if dx != 0 or dy != 0:
            self.anim_index = (self.anim_index + 0.1) % 3
        else:
            self.anim_index = 0

        if self.dir == "right":
            self.image = self.walk_right[int(self.anim_index)]
        elif self.dir == "left":
            self.image = self.walk_left[int(self.anim_index)]

        elif self.dir == "front":
            self.image = self.walk_front[int(self.anim_index)]
        elif self.dir == "back":
            self.image = self.walk_back[int(self.anim_index)]

        # Kustība ar kolīziju
        next_rect = self.rect.move(dx, 0) #Tas ļauj pārbaudīt kolīzijas pirms kustības, lai nebūtu "ieraušanās sienās".
        if not any(next_rect.colliderect(r) for r in collision_rects):
            self.rect = next_rect

        next_rect = self.rect.move(0, dy)
        if not any(next_rect.colliderect(r) for r in collision_rects):
            self.rect = next_rect


# ---------------------------------------------------
# LOAD TMX MAP
# ---------------------------------------------------
tmx_data = pytmx.util_pygame.load_pygame("mape1.tmx")

map_data = pyscroll.TiledMapData(tmx_data)
map_layer = pyscroll.BufferedRenderer(map_data, screen.get_size())
map_layer.zoom = 1.0

group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=10)

# ---------------------------------------------------
# READ OBJECTS FROM TMX
# ---------------------------------------------------
collision_rects = []
triggers = []

player_start_x = 100
player_start_y = 100

player_end_x=0
player_end_y=0

for obj in tmx_data.objects:

    # Sākuma punkts
    if obj.name == "player_start":
        player_start_x = obj.x
        player_start_y = obj.y

    # Npc punkts
    if obj.name == "npc":
        npc_start_x = obj.x
        npc_start_y = obj.y

    # End punkts
    if obj.name == "player_end":
        player_end_x = obj.x
        player_end_y = obj.y


    # Kolīzijas objekti
    if obj.type == "collision" or obj.name == "collision":
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        collision_rects.append(rect)

    # Triggeri — saglabā gan rect, gan nosaukumu
    if obj.name and obj.name.startswith("trigger"):
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        triggers.append((rect, obj.name))


# ---------------------------------------------------
# CREATE PLAYER
# ---------------------------------------------------
player = Player(player_start_x, player_start_y)
group.add(player)

end_rect = pygame.Rect(player_end_x, player_end_y, 32, 32)

life_counter = 3



# ---------------------------------------------------
# MATH QUESTION FUNCTION START
# ---------------------------------------------------
def ask_math_question_screen(life_counter, difficulty):
    time_limit = 0
    start_time = pygame.time.get_ticks()

    # ===== 1. Izveido jautājumu (Bez izmaiņām) =====
    if difficulty == "easy":
        a = random.randint(1, 30)
        b = random.randint(20, 60)
        correct = a + b
        question_text = f"Cik ir {a} + {b} ?"
        time_limit = 50000
    elif difficulty == "medium":
        a = random.randint(10, 20)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        correct = (a - b * 2) ** 3 + c / 2
        question_text = f"Cik ir ({a} - {b} x 2)^3 + {c} / 2 ?"
        time_limit = 100000
    elif difficulty == "hard":
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 20)
        correct = (b ** 2 - 4 * a * c)
        question_text = f"Kāds ir diskriminants: {a}x² + {b}x + {c} ?"
        time_limit = 200000
    # ===== 2. Fonts un sagatavošana =====
    font = pygame.font.Font('freesansbold.ttf', 50)
    small = pygame.font.Font('freesansbold.ttf', 32)

    pareizi = font.render('Pareizi!', True, (0, 255, 0))
    nepareizi = font.render('Nepareizi!', True, (255, 0, 0))

    user_text = ""
    answered = False
    result = None


    # ===== 3. Ievades cikls =====
    while not answered:
        # 1. Pārbaudām laiku
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time
        remaining_time = max(0, time_limit - elapsed_time)  # Lai neaiziet mīnusā

        # JA LAIKS BEIDZIES
        if remaining_time == 0:
            life_counter -= 1  # Noņem dzīvību
            result = False  # Uzskata par nepareizu
            answered = True  # Beidz ciklu
            # Vari šeit pievienot tekstu "Laiks beidzās!"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return life_counter, False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    safe_text = user_text.replace(",", ".")
                    try:
                        user_value = float(safe_text)
                    except:
                        user_value = None

                    if user_value is not None and abs(user_value - correct) < 0.1:
                        result = True
                    else:
                        result = False
                        life_counter -= 1  # Šeit samazinās dzīvības

                    answered = True

                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    if event.key == pygame.K_MINUS:
                        user_text += "-"
                    elif event.key == pygame.K_PERIOD:
                        user_text += "."
                    elif event.key == pygame.K_COMMA:
                        user_text += ","
                    elif event.unicode.isdigit():
                        user_text += event.unicode

        # ===== 4. Zīmēšana =====
        screen.fill((50, 50, 50))

        # --- JAUNS: SIRSNIŅU ZĪMĒŠANA ---
        # Mēs izmantojam ciklu, lai uzzīmētu sirdi tik reizes, cik ir dzīvības
        start_x = 50  # Sākuma X koordināta
        start_y = 50  # Sākuma Y koordināta
        atstarpe = 40  # Atstarpe starp sirdīm

        for i in range(life_counter):
            # Aprēķinām katras nākamās sirds pozīciju
            x_pos = start_x + (i * atstarpe)
            screen.blit(heart_img, (x_pos, start_y))
        # -------------------------------

        q = font.render(question_text, True, (255, 255, 255))
        screen.blit(q, (850, 300))  # Pielāgo pozīciju, ja vajag, lai neiet pāri sirdīm

        ans = font.render(user_text, True, (200, 200, 50))
        screen.blit(ans, (900, 450))

        screen.blit(small.render("Ievadi atbildi un spied ENTER", True, (200, 200, 200)), (750, 550))

        # 2. Uzzīmējam taimeri (SVARĪGI spēlētājam)
        # Pārveidojam sekundēs un noapaļojam
        seconds_left = int(remaining_time / 1000)
        timer_text = font.render(f"Laiks: {seconds_left}", True, (255, 100, 100))
        screen.blit(timer_text, (1600, 50))  # Labajā augšējā stūrī

        pygame.display.update()

    # ===== 5. Rezultāta logs (2 sekundes) =====
    end_time = pygame.time.get_ticks() + 2000

    while pygame.time.get_ticks() < end_time:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return life_counter, False

        screen.fill((50, 50, 50))

        # --- JAUNS: SIRSNIŅU ZĪMĒŠANA ARĪ ŠEIT ---
        # Tas ir svarīgi, lai spēlētājs redzētu, ka viena dzīvība ir pazudusi (jo life_counter jau ir samazināts)
        for i in range(life_counter):
            x_pos = 50 + (i * 40)
            screen.blit(heart_img, (x_pos, 50))
        # -----------------------------------------

        screen.blit(pareizi if result else nepareizi, (850, 450))
        pygame.display.update()

    return life_counter, True


# ---------------------------------------------------
# MATH QUESTION FUNCTION END
# ---------------------------------------------------

def load_triggers():
    trig_list = []
    for obj in tmx_data.objects:
        if obj.name and obj.name.startswith("trigger"):
            rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            trig_list.append((rect, obj.name))   # <- PIEVIENO AR NOSAUKUMU
    return trig_list


# ---------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------

label = pygame.font.Font('freesansbold.ttf', 20)
win_label = label.render('YOU WIN!', 1, (193,196,199))
lose_label = label.render('YOU LOSE!', 1, (193,196,199))
restart_label = label.render('RESTART', 1, (115,132,148))
exit_label = label.render('EXIT', 1, (115,132,148))
restart_label_rect = restart_label.get_rect(topleft=(1920/2,(1080/2)+50))
exit_label_rect = exit_label.get_rect(topleft=(1920/2,(1080/2)+100))

def screenFule():
    screen.fill((87, 88, 89))
    screen.blit(win_label, (1920 / 2, 1080 / 2))
    screen.blit(restart_label, restart_label_rect)
    screen.blit(exit_label, exit_label_rect)

def nscreenLoose():
    screen.fill((87, 88, 89))
    screen.blit(lose_label, (1920 / 2, 1080 / 2))
    screen.blit(restart_label, restart_label_rect)
    screen.blit(exit_label, exit_label_rect)


screen_center =(1920 / 2, 1080 / 2)

running = True
gameplay =True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if gameplay:

        # Update player
        player.update(collision_rects)
        group.center(player.rect.center)

        # Trigger pārbaude
        for rect, name in triggers:
            if player.rect.colliderect(rect):
                # nosaki grūtību no vārda
                if name.startswith("triggerH"):
                    difficulty = "hard"
                elif name.startswith("triggerM"):
                    difficulty = "medium"
                else:
                    difficulty = "easy"

                life_counter, gameplay = ask_math_question_screen(life_counter, difficulty)
                triggers.remove((rect, name))

                if life_counter <= 0:
                    gameplay = False
                break
        if player.rect.colliderect(end_rect):
            gameplay = False
        # Zīmēšana
        group.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    # Spēle beidzas
    else:
        # Ja mēs zaudējām dzīvības
        if life_counter <=0 and gameplay == False:
            nscreenLoose()

            #Ja mēs aizgājam līdz finišam
        else:
            screenFule()

        mouse = pygame.mouse.get_pos()
        # Restratē spēli
        if restart_label_rect.collidepoint(mouse) and pygame.mouse.get_pressed()[0]:
            gameplay = True
            life_counter = 3
            # Pārvieto player no TMX start pozīcijas
            player = Player(player_start_x, player_start_y)
            # Atjauno triggerus
            triggers = load_triggers()

            # Atjauno Pyscroll group
            group.empty()
            group.add(player)



        elif exit_label_rect.collidepoint(mouse) and pygame.mouse.get_pressed()[0]:
            running = False
    pygame.display.update()

pygame.quit()
