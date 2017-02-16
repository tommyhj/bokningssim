from tkinter import *
import random
import time
import math
import os
from subprocess import call


SIMULATE = 0.6
# Denna konstant anger att programmet ska köras i simuleringsläge och skapar slumpmässiga bokningar när nytt datum väljs
# Högre konstant ger fler slumpmässiga bokningar

GENERATOR_LENGTH = 48
# Denna konstant anger hur långa tåg som ska genereras. En vagn har 16 platser, så jämna multiplar av 16 rekommenderas


def time_formatter(time):
	# Gör om formatet på tid från t.ex. 1200 till 12.00
	return time[:2] + "." + time[2:]

def purge():
	# Raderar bokningsfiler äldre än dagens datum
	filelist = os.listdir(path='./bookings/')
	for file in filelist:
		if int(file[-14:-12]) < int(time.strftime("%y")):
			# Om filens årtal är tidigare än aktuell årtal tas den bort
			try:
				os.remove("bookings/" + file)
				print("Raderade den inaktuella bokningsfilen", file)
			except:
				print("Kunde ej radera den inaktuella bokningsfilen", file)
		elif int(file[-14:-12]) == int(time.strftime("%y")) and int(file[-12:-10]) < int(time.strftime("%m")):
			# Om filens årtal är samma som nuvarande, men månaden är tidigare, tas den bort
			try:
				os.remove("bookings/" + file)
				print("Raderade den inaktuella bokningsfilen", file)
			except:
				print("Kunde ej radera den inaktuella bokningsfilen", file)
		elif int(file[-14:-12]) == int(time.strftime("%y")) and int(file[-12:-10]) == int(time.strftime("%m")) \
				and int(file[-10:-8]) < int(time.strftime("%d")):
			# Om filens årtal är samma som nuvarande, månaden är nuvarande och dagen är tidigare, tas den bort
			try:
				os.remove("bookings/" + file)
				print("Raderade den inaktuella bokningsfilen", file)
			except:
				print("Kunde ej radera den inaktuella bokningsfilen", file)
	return

def check_config():
	#Kontrollerar att konfigureringsfilen finns. Avslutar annars programmet
	if not os.path.exists('timetables/settings.conf'):
		print("Inställningsfilen settings.con kan inte hittas. Programmet kan ej fortsätta.")
		quit()


class train(object):
	""" Hanterar det valda tågets bokningsstatus """

	def __init__(self):
		# Dessa variabler är inte konstanter som kan användas för att ställa in programmet, de ändras under körningen
		self.seats = {} # Bokningsinformation för varje sittplats
		self.departure_time = "1900" # Avgångstiden för bokningen eller avbokningen
		self.departure_date = ["20" + time.strftime("%y"), time.strftime("%m"), time.strftime("%d")] # Avgångstiden
		self.train_line = "18 Jokkmokk - Stockholm" # Tåglinjen som man arbetar med
		self.group_size = 1 # Antalet resenärer i bokningen
		self.car_length = 10 # Hur långt tåget är, ändras av programmet beroende på platsantal
		self.car_width = 4 # Bredden på vagnarna
		self.car_division = 5 # Det radantal som ingår i varje vagn
		self.car_aisle = int(self.car_width / 2) # Den rad som markeras som mittgång

	def set_line(self, line):
		# Ställer in vilken linje som ska hanteras
		self.train_line = line
		return

	def load_train(self):
		# Laddar in bokningsfilen för det valda tågnumret, datumet och tiden
		try:
			booking_file = open("bookings/" + str(self.train_line) + self.departure_date[0] + self.departure_date[1] +
								self.departure_date[2] + self.departure_time + ".dat", "r")
		except:
			self.train_generator()
			booking_file = open("bookings/" + str(self.train_line) + self.departure_date[0] + self.departure_date[1] +
								self.departure_date[2] + self.departure_time + ".dat", "r")
		lines = booking_file.readlines()
		for line in lines:
			if "#" not in line:
				self.seats.update({int(line.split(":")[1]): int(line.split(":")[3].rstrip())})

	def car_geometry(self):
		# Definierar vagnens längd och bredd utifrån platsantalet
		self.car_length = math.ceil(len(self.seats)/4)
			#math.ceil((len(self.seats) + math.ceil(self.car_width // 2)) // self.car_width)
		self.car_aisle = int(self.car_width / 2)

	def timetable_lookup(self, date):
		# Returnerar tillgängliga tågtiderna för det valda datumet som lista eller returnerar false om inga finns
		try:
			table_file = open("timetables/" + str(self.train_line) + ".dat", "r")
		except:
			print("Tidtabell saknas. Bokningen kan ej fortsätta.")
			return False
		if (int(date[0]) - 2000) < int(time.strftime("%y")):
			print("Avgångsdatumet har passerat")
			return False
		elif (int(date[0]) - 2000) == int(time.strftime("%y")) and int(date[1]) < int(time.strftime("%m")):
			print("Avgångsdatumet har passerat")
			return False
		elif (int(date[0]) - 2000) == int(time.strftime("%y")) and int(date[1]) == int(time.strftime("%m")) and \
						int(date[2]) < int(time.strftime("%d")):
			print("Avgångsdatumet har passerat")
			return False
		lines = table_file.readlines()
		avaliable_time = []
		for line in lines:
			if "#" not in line:
				if line.startswith(date[0] + "-" + date[1] + "-" + date[2] + ":"):
					avaliable_time.append(line.split(":")[1].rstrip())
				elif line.startswith(date[0] + "-" + "00" + "-" + date[2] + ":"):
					avaliable_time.append(line.split(":")[1].rstrip())
				elif line.startswith(date[0] + "-" + date[1] + "-" + "00" + ":"):
					avaliable_time.append(line.split(":")[1].rstrip())
				elif line.startswith(date[0] + "-" + "00" + "-" + "00" + ":"):
					avaliable_time.append(line.split(":")[1].rstrip())
				elif line.startswith(date[0] + "-" + date[1] + "-" + date[2] + "X"):
					if "----" in line:
						return False
					try:
						avaliable_time.remove(line.split("X")[1].rstrip())
					except:
						pass
		table_file.close()
		return avaliable_time

	def train_generator(self):
		#Skapar en bokningsfil för tåg vid vald tidpunkt
		if not (os.path.isdir("./bookings")):
			# Kontrollerar att bokningskatalogen finns och skapar den om den saknas
			os.makedirs("./bookings")

		booking_file = open("bookings/" + str(self.train_line) + self.departure_date[0] + self.departure_date[1]
							+ self.departure_date[2] + self.departure_time + ".dat", "w+")
		booking_file.write("# Bokningsfil för linje " + self.train_line + " " + self.departure_date[0] + "-" + \
						 self.departure_date[1] + "-" + self.departure_date[2] + " " + self.departure_time + "\n")
		for i in range(1, GENERATOR_LENGTH+1):
			booking_file.write("Plats:" + str(i) + ": ")
			booking_file.write("Bokningsstatus:" + str(round(SIMULATE * random.random())) + "\n")
		booking_file.close()

	def seat_availability(self, seat):
		#Kontrollerar bokningsstatus för en sittplats, observera att true betyder tillgänglig
		if self.seats[seat] == 1:
			return False
		else:
			return True

	def seat_suggestion(self, group):
		#Tar fram förslag på placering för sammanhållen bokning (returnerar platserna som lista)
		seats_in_group = [0]
		for i in range(1, len(self.seats)):
			if group == 1 and self.seat_availability(i):
				# Om gruppen bara har en medlem, returneras första lediga plats
				return [i]

			elif group == 2 and self.seat_availability(i) and self.seat_availability(i + 1):
				# Om gruppen har två medlemmar returneras ett förslag när två lediga platser brevid varandra hittas
				if i % 2 == 1:
					seats_in_group.append(i)
					seats_in_group.append(i + 1)
					return seats_in_group[1:]

			elif group > 2 and self.seat_availability(i) and i % 2 == 1:
				# Detta stycke hanterar en grupp med mer än två medlemmar. Där reglerna är att den första platsen inte
				# ska vara ensam, och att alla platser ska vara i samma vagn och på samma sida om mittgången
				for j in range(group):
					if i + j < len(booking.seats):
						if self.seat_availability(i + j) and i // ((booking.car_division-1) * 2) == (i + j-1) // (
									(booking.car_division - 1) * 2):
							seats_in_group.append(i + j)
				if len(seats_in_group) >= group + 1:
					return seats_in_group[1:]
				seats_in_group = [0]
		return False

	check_config()

	def save_train(self):
		""" Sparar bokningsstatus till det aktuella tågets bokningsfil """
		print("Sparar bokningsstatus till det aktuella tågets bokningsfil")
		booking_file = open(
			"bookings/" + str(self.train_line) + self.departure_date[0] + self.departure_date[1] + \
			self.departure_date[2] + self.departure_time + ".dat", "w+")
		booking_file.write(
			"# Bokningsfil för linje " + self.train_line + " " + self.departure_date[0] + "-" + self.departure_date[1] \
			+ "-" + self.departure_date[2] + " " + self.departure_time + "\n")
		for i in range(1, len(booking.seats)+1):
			booking_file.write("Plats:" + str(i) + ": ")
			booking_file.write("Bokningsstatus:" + str(self.seats[i]) + "\n")
		booking_file.close()


def list_line():
	''' Returnerar en lista på tillgänliga linjer, utifrån timetables/settings.conf'''
	try:
		line_list = open("timetables/settings.conf", "r")
	except:
		quit()
	lines = line_list.readlines()
	line_list.close()
	available_lines = []
	if not lines:
		print("Inställningsfilen settings.conf kan ej läsas korrekt. Programmet avslutas")
		quit()
	for line in lines:
		if "#" not in line:
			available_lines.append(line.rstrip())
	return available_lines


def about():
	'''Om-fönstret i hjälpmenyn'''
	about_win = Toplevel()
	T = Text(about_win, height=2, width=30)
	T.pack()
	T.insert(END, "Platsbokning 1.0 \n")
	button = Button(about_win, text="Ok", command=about_win.destroy)
	button.pack()


class booking_gui(Tk, train):
	#Huvudklassen för den grafiska menyn, innehåller menyerna högst upp på skärmen

	def __init__(self, *args, **kwargs):
		Tk.__init__(self, *args, **kwargs)
		menubar = Menu()
		file_menu = Menu(menubar, tearoff=0)
		file_menu.add_command(label="Avsluta", command=quit)
		menubar.add_cascade(label="Arkiv", menu=file_menu)
		help_menu = Menu(menubar, tearoff=0)
		help_menu.add_command(label="Om...", command=about)
		menubar.add_cascade(label="Hjälp", menu=help_menu)
		Tk.config(self, menu=menubar)
		Tk.title(self, "Platsbokning 1.0")
		container = Frame(self)
		container.pack(side="top", fill="both", expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)
		self.frames = {}
		for F in (Packer, Grid):
			# Hanterare för de olika grafikkontrollerna, pack och grid
			frame = F(container, self)
			self.frames[F] = frame
			frame.grid(row=0, column=0, sticky="nsew")
		self.show_frame(Packer)

	def show_frame(self, cont):
		#Uppdaterar innehållet i huvudfönstret genom att växla mellan Grid och Pack
		frame = self.frames[cont]
		frame.tkraise()
		frame.update()


class Packer(Frame):
	#Klass för att hantera de sidor som använder Pack

	def __init__(self, parent, controller):
		self.widget_list = [] # Innehåller listan med widgets som skapats i denna klass
		Frame.__init__(self, parent)

		def pack_and_return(widget, side="top", anchor="center"):
			# Funktion som packar den angivna widgeten och returnerar dess namn, så att det kan fogas till widgetlistan
			widget.pack(side=side)
			return widget

		def list_unpack():
			# Funktion som döljer samtliga widgets i widgetlistan
			for widget in self.widget_list:
				widget.pack_forget()
			self.widget_list = []
			return

		def time_chooser(date, line, unbook=FALSE):
			# Väljare för avgångstid, tar in datumet som en lista i formatet ÅÅÅÅ MM DD.

			def radio_btn(RadioButton, radioiterand, TimeList):
				# Avmarkerar övriga radioknappar, sätter radiovar till det valda värdet och aktiverar Gå-vidare
				for button in RadioButton:
					button.deselect()
				RadioButton[radioiterand].select()
				DateChoosen.config(state=NORMAL)
				booking.departure_time = TimeList[radioiterand]

			booking.train_line = line
			list_unpack() # Rensar bort eventuella widgets som blivit kvar
			if booking.timetable_lookup(date):
				# IF-satsen kontrollerar att det verkligen finns avgångar på det valda datumet
				InfoText = Label(self, text="Välj mellan följande avgångstider:")
				self.widget_list.append(pack_and_return(InfoText))
				radioiterand = 0
				RadioButton = []
				TimeList = booking.timetable_lookup(date)
				for time in TimeList:
					radiovar = IntVar()
					RadioButton.append(Radiobutton(self, text=time_formatter(time), variable=radiovar, value=time,
							command=lambda radioiterand=radioiterand: radio_btn(RadioButton, radioiterand, TimeList)))
					self.widget_list.append(pack_and_return(RadioButton[radioiterand]))
					radioiterand += 1
				if not unbook:
					DateChoosen = Button(self, text="Gå vidare för att boka",
										command=lambda: seat_choice(date, booking.departure_time), state=DISABLED)
					self.widget_list.append(pack_and_return(DateChoosen))
				if unbook:
					DateChoosen = Button(self, text="Gå vidare för att avboka", command=lambda: unbooker(),
										state=DISABLED)
					self.widget_list.append(pack_and_return(DateChoosen))
				booking.departure_date = date
				booking.load_train() # Laddar in bokningsdata för det aktuella tåget, eftersom vi bytt avgång
			else:
				InfoText = Label(self, text="Det finns inga avgångstider den dagen")
				self.widget_list.append(pack_and_return(InfoText))
				DateButton = Button(self, text="Välj ett nytt datum", command=lambda: date_chooser())
				self.widget_list.append(pack_and_return(DateButton))
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", command=lambda: welcome_page())
			self.widget_list.append(pack_and_return(MainMenu))
			return

		def seat_choice(date=booking.departure_date, time=booking.departure_time):
			# Överlämnar kontrollen åt Grid-klassen och återställer Packer-klassen till utgångläget
			list_unpack() # Rensar bort eventuella widgets som blivit kvar
			controller.show_frame(Grid)
			welcome_page()

		def unbooker():
			# Ger användaren möjlighet att välja vilka platser som ska avbokas med kryssboxar
			list_unpack()
			booking.load_train()

			# För att kunna hantera extremt många samtidiga avbokningar så delas kryssboxarna in i tre ramar
			top_frame = Frame(self)
			self.widget_list.append(pack_and_return(top_frame, anchor="top"))
			bottom_frame = Frame(self)
			self.widget_list.append(pack_and_return(bottom_frame, anchor="bottom"))
			bottom_frame2 = Frame(self)
			self.widget_list.append(pack_and_return(bottom_frame2, anchor="bottom"))

			VarList = [0] * (len(booking.seats) + 1)
			iterand = 0
			for pick in booking.seats:
				# For-loopen renderar kryssboxarna
				VarList[pick] = IntVar()
				if booking.seats[pick]:
					iterand += 1
					if iterand < 20:
						chk = Checkbutton(top_frame, text=pick, variable=VarList[pick], onvalue=1)
					elif iterand < 40:
						chk = Checkbutton(bottom_frame, text=pick, variable=VarList[pick], onvalue=1)
					else:
						chk = Checkbutton(bottom_frame2, text=pick, variable=VarList[pick], onvalue=1)
					self.widget_list.append(pack_and_return(chk, side="left"))

			def normalise_varlist(VarList):
				# Gör om strängvariablerna i Varlist till en normal lista
				normalised_list = []
				for i in range(0, len(VarList)):
					if VarList[i].get():
						normalised_list.append(i)
				return normalised_list

			def commit_unbook(unbooking_list):
				# Sparar valda avbokningar
				list_unpack()
				for seat in unbooking_list:
					booking.seats[seat + 1] = 0
				booking.save_train()
				welcome_page()

			if 1 in booking.seats.values():
				# Visa avbokningsknapp om bokningar finns, vilket if-satsen kontrollerar
				UnbookCommit = Button(self, text="Spara avbokningar och gå till huvudmenyn",
								command=lambda: commit_unbook((normalise_varlist(VarList[1:]))))
				self.widget_list.append(pack_and_return(UnbookCommit))
			else:
				# Visa meddelande om inga bokningar finns
				EmptyUnbook = Label(self, text="Det finns inga bokningar att avboka")
				self.widget_list.append(pack_and_return(EmptyUnbook))

			MainMenu = Button(self, text="Tillbaka till huvudmenyn", command=lambda: welcome_page())
			self.widget_list.append(pack_and_return(MainMenu))
			return

		def welcome_page():
			# Innehåller välomstmeddelande och huvudmeny
			list_unpack() # Rensar bort eventuella widgets som blivit kvar

			WelcomeText = Label(self, text="Välkommen till platsbokningen. Välj ett alternativ:")
			WelcomeText.pack(pady=10, padx=10)
			self.widget_list.append(WelcomeText)

			NewBookingButton = Button(self, text="Ny bokning", command=lambda: date_chooser())
			self.widget_list.append(pack_and_return(NewBookingButton))

			UnBookingButton = Button(self, text="Avbokning", command=lambda: date_chooser(unbook=True))
			self.widget_list.append(pack_and_return(UnBookingButton))

			ExitButton = Button(self, text="Avsluta", command=quit)
			self.widget_list.append(pack_and_return(ExitButton))
			return

		def date_chooser(unbook=FALSE):
			# Visar väljaren för avresedatum
			list_unpack()

			LineText = Label(self, text="Välj tåglinje:" )
			self.widget_list.append(pack_and_return(LineText))

			choice_lines = StringVar(self)
			choice_lines.set(list_line()[0])
			LineOption = OptionMenu(self, choice_lines, *list_line())
			self.widget_list.append(pack_and_return(LineOption))

			DepartureText = Label(self, text="Välj önskad avgång:")
			self.widget_list.append(pack_and_return(DepartureText))
			month = StringVar(self)
			month.set(str(time.strftime("%m"))) # Begynnelsevärdet för månadsväljaren anges till aktuell månad
			day = StringVar(self)
			day.set(str(time.strftime("%d"))) # Begynnelsevärdet för datumväljaren anges till dagens datum
			year = StringVar(self)
			year.set("20" + time.strftime("%y")) # Begynnelsevärdet för årsväljaren anges till aktuellt år
			YearOption = OptionMenu(self, year, "20" + time.strftime("%y"), str(2001 + int(time.strftime("%y"))))
			# Ger årsväljaren alternativen det aktuella året samt ett år framåt.
			self.widget_list.append(pack_and_return(YearOption))
			MonthOption = OptionMenu(self, month, "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12")
			self.widget_list.append(pack_and_return(MonthOption))
			DayOption = OptionMenu(self, day, "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
								"13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26",
								"27", "28", "29", "30", "31")
			self.widget_list.append(pack_and_return(DayOption))
			if not unbook:
				TimeChooserButton = Button(self, text="Gå vidare och boka", command=lambda: time_chooser([year.get(),
											month.get(), day.get()], choice_lines.get()))
				self.widget_list.append(pack_and_return(TimeChooserButton))
			else:
				TimeChooserButton = Button(self, text="Gå vidare och avboka", command=lambda: time_chooser([year.get(),
												month.get(), day.get()], choice_lines.get(), True))
				self.widget_list.append(pack_and_return(TimeChooserButton))
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", command=lambda: welcome_page())
			self.widget_list.append(pack_and_return(MainMenu))
			return

		welcome_page()


class Grid(Frame):
	#Hanterar sidor som använder grid

	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.widget_list = []
		self.booking_progress = []
		self.seat_button = [0]

		def grid_and_return(widget, row=0, column=0, columnspan=1, sticky="", padx="1", pady="1", ipadx="1", ipady="1"):
			# Sätter widgeten i grid:en returnerar namnet, så att det kan fogas till widgetlistan
			widget.grid(row=row, column=column, columnspan=columnspan, sticky=sticky, padx=padx, pady=pady, ipadx=ipadx,
						ipady=ipady)
			self.widget_list.append(widget)
			return

		def list_ungrid():
			# Funktion som döljer samtliga widgets i widgetlistan
			for widget in self.widget_list:
				widget.grid_forget()
			self.widget_list = []
			return

		def clean_return():
			# Funktion för att lämna grid och gå tillbaka till pack utan att lämna kvar widgets
			unmark_all()
			list_ungrid()
			controller.show_frame(Packer)
			group_booking()

		def mark_seat(seat_increment):
			# Markerar platser som ska bokas med asterisker
			self.seat_button[seat_increment].configure(text="* " + str(seat_increment) + " *",
				command=lambda seat_increment=seat_increment: unmark_seat(seat_increment))
			self.booking_progress.append(seat_increment)
			return

		def unmark_seat(seat_increment):
			# Avmarkerar platser i bokningsprocessen.
			try:
				self.seat_button[seat_increment].configure(text=str(seat_increment),
				command=lambda seat_increment=seat_increment: mark_seat(seat_increment))
			except:
				return
			try:
				self.booking_progress.remove(seat_increment)
				return
			except:
				return

		def unmark_all():
			# Avmarkerar alla platser i bokningsgrafiken
			for i in range(1, len(booking.seats) + 1):
				unmark_seat(i)
			return

		def gui_seat_suggest(group):
			# Markerar upp föreslagna sittplatser i det grafiska gränssnittet och returnerar en lista på dem
			display_seats()
			unmark_all()
			# Rensar bort eventuella befintliga markeringar
			for i in range(1, len(self.seat_button)):
				unmark_seat(i)
			self.booking_progress = []

			if booking.seat_suggestion(group):
				for i in booking.seat_suggestion(group):
					mark_seat(i)
			else:
				# Skapar ett popupfönster om platsförslag misslyckas
				fail_popup = Toplevel()
				fail_text = Text(fail_popup, height=2, width=30, padx=10, pady=10)
				fail_text.pack()
				fail_text.insert(END, "Det finns ej nog många\nsammanhängande platser.")
				button1 = Button(fail_popup, text="Föreslå spridda platser", command=lambda: fallback_seating(group))
				button1.pack()
				button2 = Button(fail_popup, text="Ok", command=fail_popup.destroy)
				button2.pack()
			return

		def fallback_seating(group):
			# Föreslår spridda platser, avsedd att användas när programmet inte kan få ihop en sammanhållen bokning
			marked = 0
			for i in range(1, len(booking.seats)+1):
				if booking.seat_availability(i):
					mark_seat(i)
					marked += 1
					if marked == group:
						break
			return True

		def display_seats():
			# Renderar en bild av bokningsläget
			list_ungrid()
			booking.load_train()
			booking.car_geometry()
			# Ser till att all information om vagnens dimensioner är aktuell
			aisle = booking.car_aisle
			seat_increment = 0

			while seat_increment < len(booking.seats):
				for i in range(0, booking.car_length + math.ceil(booking.car_length / booking.car_division)):

					if i % booking.car_division == 0:
						# Genererar rad med vagnsnummer om vagnslängden är nådd
						CarLabel = Label(self, text="Vagn" + str((i) // booking.car_division + 1), borderwidth=1)
						if not i == booking.car_length:
							grid_and_return(CarLabel, row=i + 2, column=aisle - 1, columnspan=3)
					else:
						if seat_increment < (len(booking.seats) // 2):
							render_end = aisle + 1
							render_start = 0
						elif seat_increment >= (len(booking.seats) // 2):
							render_start = aisle + 1
							render_end = booking.car_width + 1
						for j in range(render_start, render_end):
							if j == aisle:
								AisleButton = Button(self, text=" - ", borderwidth=2, width=5, relief="raised",
													state=DISABLED)
								grid_and_return(AisleButton, row=i + 2, column=aisle)
							elif seat_increment < len(booking.seats):
								seat_increment += 1
								if seat_increment > len(booking.seats):
									break
								self.seat_button.append(
									Button(self, text=str(seat_increment), borderwidth=2, width=5,
									relief="raised", state=ACTIVE,
									command=lambda seat_increment=seat_increment: mark_seat(seat_increment)))
								if booking.seats[seat_increment] == 0:
									self.seat_button[seat_increment].configure(state=ACTIVE)
								else:
									self.seat_button[seat_increment].configure(state=DISABLED)
								grid_and_return(self.seat_button[seat_increment], row=i + 2, column=j)
			InstructionLabel = Label(self, text="Klicka för att välja plats.")
			grid_and_return(InstructionLabel, column=0, columnspan=4, row=99)
			group = IntVar(self)
			group.set(1) # Begynnelsevärdet för Gruppstorlek
			GroupLabel = Label(self, text="För platsförslag, välj antal:")
			grid_and_return(GroupLabel, column=0, columnspan=3, row=100)
			GroupOption = OptionMenu(self, group, 1, 2, 3, 4, 5, 6, 7, 8)
			grid_and_return(GroupOption, column=3, row=100)
			GroupButton = Button(self, text="Ok", borderwidth=2, width=5, relief="raised", state=ACTIVE,
								command=lambda: gui_seat_suggest(group.get()))
			grid_and_return(GroupButton, column=4, row=100)
			MoveOnButton = Button(self, text="Gå vidare och boka", borderwidth=2, width=15, relief="raised",
								state=ACTIVE, command=lambda: booking_check(booking.departure_date,
								booking.departure_time, booking.train_line))
			grid_and_return(MoveOnButton, column=0, columnspan=5, row=101)
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", borderwidth=2, relief="raised",
							  state=ACTIVE, command=lambda: clean_return())
			grid_and_return(MainMenu, row=102, columnspan=5)
			QuitButton = Button(self, text="Avsluta", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: quit())
			grid_and_return(QuitButton, row=103, columnspan=5)

		def booking_check(date, time, line):
			# Kontrollerar att användaren valt platser att boka och ger annars ett varningsmeddelande
			if not self.booking_progress:
				fail_popup = Toplevel()
				fail_text = Text(fail_popup, height=2, width=30, padx=10, pady=10)
				fail_text.pack()
				fail_text.insert(END, "Du måste välja minst en\nplats att boka")
				button = Button(fail_popup, text="Ok", command=fail_popup.destroy)
				button.pack()
			else:
				booking_confirmation(date, time, line)

		def booking_confirmation(date, time, line):
			# Ger användaren möjlighet att granska och bekräfta sin bokning, samt spara eller skriva ut.
			list_ungrid()
			InstructionLabel1 = Label(self, text="Du håller på att göra föjande bokning:")
			grid_and_return(InstructionLabel1, row=1)

			InstructionLabel1 = Label(self, text="Tåglinje: " + str(line))
			grid_and_return(InstructionLabel1, row=2)
			InstructionLabel1 = Label(self, text=str(date[0]) + "-" + str(date[1])\
												+ "-" + str(date[2]) + " Klockan:" + str(time_formatter(time)))
			grid_and_return(InstructionLabel1, row=3)
			i = 5
			self.booking_progress.sort()
			for booking in self.booking_progress:
				i += 1
				SeatLabel = Label(self, text="Plats nummer: " + str(booking))
				if i < 25:
					grid_and_return(SeatLabel, row=i, column=0)
				elif i >= 25:
					grid_and_return(SeatLabel, row=i - 19, column=1)

			SaveButton = Button(self, text="Spara bokning", borderwidth=2, relief="raised", state=ACTIVE,
								command=lambda: confirm_and_print())
			grid_and_return(SaveButton, row=27, column=0)
			BackToSeatButton = Button(self, text="Återgå till platsväljaren", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: display_seats())
			grid_and_return(BackToSeatButton, row=28)
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: clean_return())
			grid_and_return(MainMenu, row=29)
			QuitButton = Button(self, text="Avsluta", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: quit())
			grid_and_return(QuitButton, row=30)

		def print_ticket(prnt=False):
			# Skriver biljetten till fil. Om prnt är True skrivs den ut på papper.

			SaveConfirm = Label(self, text="Sparat", fg="red")
			grid_and_return(SaveConfirm, row=29)

			# Skriver biljetten till fil, och skickar den till systemets standardskrivare om alternativet print är aktivt.
			booking_file = open("ticket.txt", "w+")
			booking_file.write("Tågbiljett - Inlandsbanan\n_______________________\n")
			booking_file.write("Linje " + str(booking.train_line) + "\n")
			booking_file.write(str(booking.departure_date[0]) + "-" + str(booking.departure_date[1]) + "-" + str(
				booking.departure_date[2]) + "\n")
			booking_file.write("Avgång " + str(time_formatter(booking.departure_time)) + "\n")
			for plats in self.booking_progress:
				booking_file.write("Plats " + str(plats) + "\n")

			# Utskrift, testad på mac, kräver dock lpr för att fungera, så om det funkar kan variera mellan OS.
			booking_file.close()
			if prnt:
				call(["lpr", "ticket.txt"])
			return

		def confirm_and_print():
			# Bekräftar bokningen och ger möjlighet att skriva ut
			list_ungrid()
			for booked in self.booking_progress:
				booking.seats[booked] = 1
			ConfirmedLabel = Label(self,
								text="Den bokning är nu bekräftad. Tryck på Skriv ut för att skriva ut din biljett.")
			grid_and_return(ConfirmedLabel, row=1)
			PrintButton = Button(self, text="Spara biljett utan att skriva ut", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: print_ticket())
			grid_and_return(PrintButton, row=2)
			PrintButton = Button(self, text="Spara och Skriv ut", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: print_ticket(True))
			grid_and_return(PrintButton, row=3)
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: clean_return())
			grid_and_return(MainMenu, row=4)
			QuitButton = Button(self, text="Avsluta", borderwidth=2, relief="raised",
								state=ACTIVE,command=lambda: quit())
			grid_and_return(QuitButton, row=5)
			booking.save_train()
			return

		def group_booking():
			# Ger användaren möjlighet att ange antal för automatiskt platsförslag eller gå vidare till manuell
			group = IntVar(self)
			group.set(1) # Begynnelsevärdet för Gruppstorlek
			GroupLabel = Label(self, text="För att få automatiskt platsförslag, välj antal:")
			grid_and_return(GroupLabel, column=1, row=1)
			GroupOption = OptionMenu(self, group, 1, 2, 3, 4, 5, 6, 7, 8)
			grid_and_return(GroupOption, column=2, row=1)
			GroupButton = Button(self, text="Ok", borderwidth=2, relief="raised", state=ACTIVE,
								command=lambda: gui_seat_suggest(group.get()))
			grid_and_return(GroupButton, column=3, row=1)
			BookingButton = Button(self, text="Visa bokningsstatus och välj plats manuellt",
								command=lambda: display_seats())
			grid_and_return(BookingButton, column=1, row=3)
			MainMenu = Button(self, text="Tillbaka till huvudmenyn", borderwidth=2, relief="raised",
							  state=ACTIVE, command=lambda: clean_return())
			grid_and_return(MainMenu, row=4, columnspan=3)
			QuitButton = Button(self, text="Avsluta", borderwidth=2, relief="raised",
								state=ACTIVE, command=lambda: quit())
			grid_and_return(QuitButton, row=5, columnspan=3)

		group_booking()

booking = train()
gui_app = booking_gui()
gui_app.mainloop()
