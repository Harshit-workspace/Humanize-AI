import csv
import threading
import re
import math
from tkinter import filedialog
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    initialize_database,
    save_analysis,
    get_history,
    delete_history_item
)

from detector import AIDetector
from humanizer import humanize_text

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ----------------------------------
# APPLICATION SETTINGS
# ----------------------------------

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class HumanTextApp:

    def __init__(self, root):

        self.root = root
        self.root.title("HumanText AI")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 650)
        self.root.configure(fg_color="#F4F7FC")

        self.humanizer_busy = False
        self.humanizer_request_id = 0

        initialize_database()

        self.detector = AIDetector()
        self.model_status = "AI Detector Ready"

        try:
            self.detector.train()
        except Exception as error:
            self.model_status = f"Detector Error: {error}"

        self.create_interface()

    # ----------------------------------
    # MAIN INTERFACE
    # ----------------------------------

    def create_interface(self):

        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color="#F4F7FC",
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            width=225,
            fg_color="#FFFFFF",
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="HumanText AI",
            font=("Arial", 23, "bold"),
            text_color="#1769E0"
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            self.sidebar,
            text="AI Writing Assistant",
            font=("Arial", 11),
            text_color="#8492A6"
        ).pack(pady=(0, 30))

        self.nav_buttons = {}

        navigation = [
            ("Analytics Dashboard", self.show_dashboard),
            ("AI Detector", self.show_detector),
            ("Humanizer", self.show_humanizer),
            ("History", self.show_history),
            ("Model Performance", self.show_performance)
        ]

        for name, command in navigation:

            button = ctk.CTkButton(
                self.sidebar,
                text=name,
                height=43,
                corner_radius=9,
                anchor="w",
                fg_color="transparent",
                hover_color="#E8F1FF",
                text_color="#34445C",
                font=("Arial", 12),
                command=command
            )

            button.pack(fill="x", padx=13, pady=4)
            self.nav_buttons[name] = button

        ctk.CTkLabel(
            self.sidebar,
            text="VERSION 1.3",
            font=("Arial", 10),
            text_color="#A0AABC"
        ).pack(side="bottom", pady=20)

        self.content = ctk.CTkFrame(
            self.main_frame,
            fg_color="#F4F7FC",
            corner_radius=0
        )
        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.show_dashboard()

    # ----------------------------------
    # PAGE MANAGEMENT
    # ----------------------------------

    def clear_content(self):

        for widget in self.content.winfo_children():
            widget.destroy()

    def update_navigation(self, active):

        for name, button in self.nav_buttons.items():

            if name == active:
                button.configure(
                    fg_color="#1769E0",
                    text_color="#FFFFFF",
                    hover_color="#1257BC"
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color="#34445C",
                    hover_color="#E8F1FF"
                )

    def create_page_header(self, title, subtitle):

        ctk.CTkLabel(
            self.content,
            text=title,
            font=("Arial", 27, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            self.content,
            text=subtitle,
            font=("Arial", 12),
            text_color="#8492A6"
        ).pack(anchor="w", padx=30, pady=(0, 15))

    def create_card(self, parent):

        return ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=13,
            border_width=1,
            border_color="#E4EAF2"
        )

    # ----------------------------------
    # DATA SUMMARY
    # ----------------------------------

    def get_analytics(self):

        records = get_history()

        total = len(records)
        ai_count = 0
        human_count = 0
        edit_count = 0

        for row in records:

            prediction = str(row[2]).lower()

            if "readability" in prediction or "edit" in prediction:
                edit_count += 1
            elif "ai" in prediction:
                ai_count += 1
            elif "human" in prediction:
                human_count += 1

        return {
            "records": records,
            "total": total,
            "ai": ai_count,
            "human": human_count,
            "edits": edit_count
        }

    # ----------------------------------
    # ANALYTICS DASHBOARD
    # ----------------------------------

    def show_dashboard(self):

        self.clear_content()
        self.update_navigation("Analytics Dashboard")

        self.create_page_header(
            "Analytics Dashboard",
            "An overview of your HumanText AI activity."
        )

        data = self.get_analytics()

        cards_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        cards_frame.pack(fill="x", padx=20, pady=5)

        for column in range(4):
            cards_frame.grid_columnconfigure(column, weight=1)

        statistics = [
            ("Total Analyses", data["total"]),
            ("AI-like Predictions", data["ai"]),
            ("Human-like Predictions", data["human"]),
            ("Writing Edits", data["edits"])
        ]

        for index, (name, value) in enumerate(statistics):

            card = self.create_card(cards_frame)
            card.grid(
                row=0,
                column=index,
                padx=7,
                pady=8,
                sticky="nsew"
            )

            ctk.CTkLabel(
                card,
                text=name,
                font=("Arial", 12),
                text_color="#8492A6"
            ).pack(anchor="w", padx=15, pady=(17, 5))

            ctk.CTkLabel(
                card,
                text=str(value),
                font=("Arial", 27, "bold"),
                text_color="#1769E0"
            ).pack(anchor="w", padx=15, pady=(0, 17))

        charts_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        charts_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)

        donut_card = self.create_card(charts_frame)
        donut_card.grid(
            row=0,
            column=0,
            padx=7,
            pady=7,
            sticky="nsew"
        )

        ctk.CTkLabel(
            donut_card,
            text="Prediction Distribution",
            font=("Arial", 15, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=15, pady=(15, 0))

        figure1 = Figure(
            figsize=(4.2, 3.0),
            dpi=90,
            facecolor="#FFFFFF"
        )

        axis1 = figure1.add_subplot(111)

        if data["ai"] + data["human"] > 0:

            axis1.pie(
                [data["ai"], data["human"]],
                labels=["AI-like", "Human-like"],
                colors=["#1769E0", "#55B98A"],
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={
                    "width": 0.42,
                    "edgecolor": "white"
                },
                textprops={"fontsize": 9}
            )

            axis1.set_title(
                "Past detector predictions",
                fontsize=10,
                color="#52627A"
            )

        else:

            axis1.text(
                0.5, 0.5,
                "No detector data yet",
                ha="center",
                va="center",
                fontsize=12,
                color="#8492A6"
            )
            axis1.axis("off")

        figure1.tight_layout()

        canvas1 = FigureCanvasTkAgg(
            figure1,
            master=donut_card
        )
        canvas1.draw()
        canvas1.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=8,
            pady=5
        )

        bar_card = self.create_card(charts_frame)
        bar_card.grid(
            row=0,
            column=1,
            padx=7,
            pady=7,
            sticky="nsew"
        )

        ctk.CTkLabel(
            bar_card,
            text="Activity Overview",
            font=("Arial", 15, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=15, pady=(15, 0))

        figure2 = Figure(
            figsize=(4.2, 3.0),
            dpi=90,
            facecolor="#FFFFFF"
        )

        axis2 = figure2.add_subplot(111)

        categories = ["AI-like", "Human-like", "Edits"]
        counts = [data["ai"], data["human"], data["edits"]]

        bars = axis2.bar(
            categories,
            counts,
            color=["#1769E0", "#55B98A", "#F0B44D"],
            width=0.55
        )

        axis2.set_ylabel("Number of records", fontsize=9)
        axis2.set_title(
            "Saved activity",
            fontsize=10,
            color="#52627A"
        )
        axis2.tick_params(axis="both", labelsize=8)
        axis2.spines["top"].set_visible(False)
        axis2.spines["right"].set_visible(False)
        axis2.grid(axis="y", alpha=0.2)
        axis2.set_axisbelow(True)

        for bar in bars:

            height = bar.get_height()

            axis2.annotate(
                str(int(height)),
                xy=(
                    bar.get_x() + bar.get_width() / 2,
                    height
                ),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                fontsize=9
            )

        figure2.tight_layout()

        canvas2 = FigureCanvasTkAgg(
            figure2,
            master=bar_card
        )
        canvas2.draw()
        canvas2.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=8,
            pady=5
        )

        recent_card = self.create_card(self.content)
        recent_card.pack(
            fill="both",
            expand=True,
            padx=27,
            pady=(5, 15)
        )

        ctk.CTkLabel(
            recent_card,
            text="Recent Activity",
            font=("Arial", 15, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=15, pady=(12, 5))

        columns = (
            "ID", "Date", "Prediction",
            "AI Probability", "Text"
        )

        recent_table = ttk.Treeview(
            recent_card,
            columns=columns,
            show="headings",
            height=4
        )

        for column in columns:
            recent_table.heading(column, text=column)

        recent_table.column("ID", width=45)
        recent_table.column("Date", width=145)
        recent_table.column("Prediction", width=120)
        recent_table.column("AI Probability", width=110)
        recent_table.column("Text", width=350)

        self.configure_table_style()

        recent_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(5, 12)
        )

        for row in data["records"][:5]:

            record_id, date, prediction, probability, preview = row

            score = (
                "—" if str(prediction).lower() == "readability edit"
                else f"{probability * 100:.1f}%"
            )

            recent_table.insert(
                "",
                "end",
                values=(
                    record_id,
                    date,
                    prediction,
                    score,
                    str(preview)[:75]
                )
            )

        if not data["records"]:

            ctk.CTkLabel(
                recent_card,
                text="Your saved analyses will appear here.",
                font=("Arial", 11),
                text_color="#8492A6"
            ).pack(pady=(0, 10))

    # ----------------------------------
    # AI DETECTOR
    # ----------------------------------

    def show_detector(self):

        self.clear_content()
        self.update_navigation("AI Detector")

        self.create_page_header(
            "AI Content Detector",
            "Analyze text and estimate how AI-like its writing patterns are."
        )

        card = self.create_card(self.content)
        card.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        ctk.CTkLabel(
            card,
            text="Enter your text",
            font=("Arial", 16, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.input_text = ctk.CTkTextbox(
            card,
            height=300,
            corner_radius=10,
            border_width=1,
            border_color="#DCE5F0",
            fg_color="#FBFCFE",
            text_color="#24344D",
            font=("Arial", 13)
        )
        self.input_text.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        ctk.CTkButton(
            card,
            text="Analyze Text",
            height=45,
            font=("Arial", 14, "bold"),
            command=self.check_ai
        ).pack(anchor="w", padx=20, pady=12)

        self.result_label = ctk.CTkLabel(
            card,
            text="Your analysis result will appear here.",
            font=("Arial", 15, "bold"),
            text_color="#1769E0"
        )
        self.result_label.pack(anchor="w", padx=20, pady=10)

        ctk.CTkLabel(
            card,
            text="Experimental estimate only — not proof of authorship.",
            font=("Arial", 11),
            text_color="#8492A6"
        ).pack(anchor="w", padx=20, pady=(0, 15))

    def check_ai(self):

        text = self.input_text.get("1.0", "end").strip()

        if not text:
            messagebox.showwarning(
                "Warning",
                "Please enter some text."
            )
            return

        try:

            probability, prediction = self.detector.predict(text)

            self.result_label.configure(
                text=(
                    f"{prediction}: "
                    f"{probability * 100:.1f}% estimated AI likelihood"
                )
            )

            save_analysis(text, probability, prediction)
            self.refresh_history()

        except Exception as error:

            messagebox.showerror(
                "Analysis Error",
                str(error)
            )

    # ----------------------------------
    # HUMANIZER
    # ----------------------------------

    def show_humanizer(self):

        self.clear_content()
        self.update_navigation("Humanizer")

        self.create_page_header(
            "Writing Assistant",
            "Compare your original writing with the improved version side by side."
        )

        card = self.create_card(self.content)
        card.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 18)
        )

        top_controls = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        top_controls.pack(
            fill="x",
            padx=18,
            pady=(15, 8)
        )

        ctk.CTkLabel(
            top_controls,
            text="Writing style:",
            font=("Arial", 13, "bold"),
            text_color="#34445C"
        ).pack(side="left", padx=(0, 8))

        self.style = ctk.StringVar(value="Clear and natural")

        ctk.CTkComboBox(
            top_controls,
            variable=self.style,
            values=[
                "Clear and natural",
                "Casual",
                "Academic",
                "Professional"
            ],
            width=220,
            state="readonly"
        ).pack(side="left", padx=5)

        self.improve_button = ctk.CTkButton(
            top_controls,
            text="Improve Writing",
            height=36,
            command=self.rewrite_text
        )
        self.improve_button.pack(side="left", padx=10)

        self.humanizer_status = ctk.CTkLabel(
            top_controls,
            text="Ready",
            font=("Arial", 11),
            text_color="#8492A6"
        )
        self.humanizer_status.pack(side="left", padx=8)

        comparison_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        comparison_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=8
        )

        comparison_frame.grid_columnconfigure(0, weight=1)
        comparison_frame.grid_columnconfigure(1, weight=1)
        comparison_frame.grid_rowconfigure(0, weight=1)

        original_panel = self.create_card(comparison_frame)
        original_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=6,
            pady=5
        )

        ctk.CTkLabel(
            original_panel,
            text="Original Text",
            font=("Arial", 15, "bold"),
            text_color="#172B4D"
        ).pack(anchor="w", padx=12, pady=(12, 5))

        self.original_text = ctk.CTkTextbox(
            original_panel,
            height=300,
            border_width=1,
            border_color="#DCE5F0",
            fg_color="#FBFCFE",
            text_color="#24344D",
            font=("Arial", 13),
            wrap="word"
        )
        self.original_text.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(4, 10)
        )

        # Live writing statistics
        self.writing_stats = ctk.CTkLabel(
            original_panel,
            text=(
                "Words: 0  |  Characters: 0  |  Sentences: 0  |  "
                "Paragraphs: 0  |  Reading time: 0 min"
            ),
            font=("Arial", 10),
            text_color="#8492A6"
        )
        self.writing_stats.pack(
            anchor="w",
            padx=12,
            pady=(0, 5)
        )

        # Live readability score
        self.readability_label = ctk.CTkLabel(
            original_panel,
            text="Readability: Enter text to calculate your score.",
            font=("Arial", 11, "bold"),
            text_color="#1769E0",
            wraplength=480,
            justify="left"
        )
        self.readability_label.pack(
            anchor="w",
            padx=12,
            pady=(0, 12)
        )

        self.original_text._textbox.bind(
            "<KeyRelease>",
            self.update_writing_statistics,
            add="+"
        )

        self.original_text._textbox.configure(
            undo=True,
            maxundo=-1,
            autoseparators=True
        )

        improved_panel = self.create_card(comparison_frame)
        improved_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=6,
            pady=5
        )

        ctk.CTkLabel(
            improved_panel,
            text="Improved Text",
            font=("Arial", 15, "bold"),
            text_color="#1769E0"
        ).pack(anchor="w", padx=12, pady=(12, 5))

        self.rewritten_text = ctk.CTkTextbox(
            improved_panel,
            height=330,
            border_width=1,
            border_color="#DCE5F0",
            fg_color="#FBFCFE",
            text_color="#24344D",
            font=("Arial", 13),
            wrap="word"
        )
        self.rewritten_text.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(4, 10)
        )

        action_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        action_frame.pack(
            fill="x",
            padx=18,
            pady=(5, 14)
        )

        ctk.CTkButton(
            action_frame,
            text="Undo",
            width=85,
            command=self.undo_input
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_frame,
            text="Redo",
            width=85,
            command=self.redo_input
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_frame,
            text="Clear All",
            width=95,
            fg_color="#DC3545",
            hover_color="#B52B38",
            command=self.clear_humanizer
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_frame,
            text="Copy Improved Text",
            width=160,
            command=self.copy_rewritten_text
        ).pack(side="right", padx=4)

        ctk.CTkLabel(
            card,
            text="The two panels let you review the original and revised wording together.",
            font=("Arial", 10),
            text_color="#8492A6"
        ).pack(anchor="w", padx=22, pady=(0, 8))

    # ----------------------------------
    # LIVE WRITING STATISTICS
    # ----------------------------------

    def update_writing_statistics(self, event=None):

        text = self.original_text.get("1.0", "end-1c")

        words = len(text.split())
        characters = len(text)

        sentences = len(re.findall(r"[.!?]+", text))

        paragraphs = len([
            paragraph
            for paragraph in re.split(r"\n\s*\n", text.strip())
            if paragraph.strip()
        ]) if text.strip() else 0

        reading_time = math.ceil(words / 200) if words else 0

        self.writing_stats.configure(
            text=(
                f"Words: {words}  |  "
                f"Characters: {characters}  |  "
                f"Sentences: {sentences}  |  "
                f"Paragraphs: {paragraphs}  |  "
                f"Reading time: {reading_time} min"
            )
        )

        # Update readability score at the same time
        self.update_readability_score(text)

    # ----------------------------------
    # READABILITY SCORE
    # ----------------------------------

    def count_syllables(self, word):

        word = word.lower()
        word = re.sub(r"[^a-z]", "", word)

        if not word:
            return 0

        # Count groups of vowels
        vowel_groups = re.findall(r"[aeiouy]+", word)

        syllables = len(vowel_groups)

        # Adjust for a silent ending e
        if word.endswith("e") and not word.endswith(
            ("le", "ye")
        ):
            if syllables > 1:
                syllables -= 1

        # Words ending in consonant + le often have an extra syllable
        if re.search(r"[^aeiou]le$", word) and len(word) > 2:
            syllables += 1

        # Every English word has at least one syllable
        return max(1, syllables)

    def calculate_readability(self, text):

        words = re.findall(
            r"[A-Za-z]+(?:['’][A-Za-z]+)?",
            text
        )

        word_count = len(words)

        if word_count == 0:
            return None

        sentences = re.findall(
            r"[^.!?]+(?:[.!?]+|$)",
            text
        )

        sentence_count = len([
            sentence
            for sentence in sentences
            if sentence.strip()
        ])

        # Avoid division by zero for text without punctuation
        sentence_count = max(1, sentence_count)

        syllable_count = sum(
            self.count_syllables(word)
            for word in words
        )

        # Flesch Reading Ease formula
        score = (
            206.835
            - 1.015 * (word_count / sentence_count)
            - 84.6 * (syllable_count / word_count)
        )

        return round(score, 1)

    def update_readability_score(self, text):

        score = self.calculate_readability(text)

        if score is None:

            self.readability_label.configure(
                text="Readability: Enter text to calculate your score.",
                text_color="#1769E0"
            )
            return

        if score >= 70:

            level = "Easy"
            explanation = (
                "Your writing is relatively easy to read."
            )
            color = "#168653"

        elif score >= 50:

            level = "Moderate"
            explanation = (
                "Your writing has a moderate reading difficulty."
            )
            color = "#D18A17"

        else:

            level = "Difficult"
            explanation = (
                "Your writing may be difficult for some readers."
            )
            color = "#DC3545"

        self.readability_label.configure(
            text=(
                f"Flesch Reading Ease: {score}/100  |  "
                f"Level: {level}\n"
                f"{explanation}\n"
                "Approximate score for English text."
            ),
            text_color=color
        )

    # ----------------------------------
    # ASYNCHRONOUS HUMANIZER
    # ----------------------------------

    def rewrite_text(self):

        text = self.original_text.get(
            "1.0", "end"
        ).strip()

        if not text:
            messagebox.showwarning(
                "Warning",
                "Please enter some text."
            )
            return

        if self.humanizer_busy:
            return

        self.humanizer_busy = True
        self.humanizer_request_id += 1

        request_id = self.humanizer_request_id
        selected_style = self.style.get()

        self.improve_button.configure(
            state="disabled",
            text="Improving..."
        )

        self.humanizer_status.configure(
            text="AI is improving your writing. Please wait...",
            text_color="#1769E0"
        )

        worker = threading.Thread(
            target=self.humanizer_worker,
            args=(text, selected_style, request_id),
            daemon=True
        )

        worker.start()

    def humanizer_worker(self, text, selected_style, request_id):

        try:

            result = humanize_text(
                text,
                selected_style
            )

            self.root.after(
                0,
                lambda: self.humanizer_success(
                    text, result, request_id
                )
            )

        except Exception as error:

            error_message = str(error)

            self.root.after(
                0,
                lambda: self.humanizer_error(
                    error_message, request_id
                )
            )

    def humanizer_success(self, original, result, request_id):

        if request_id != self.humanizer_request_id:
            return

        try:

            if not self.rewritten_text.winfo_exists():
                self.finish_humanizer()
                return

            self.rewritten_text.delete("1.0", "end")
            self.rewritten_text.insert("end", result)

            save_analysis(
                original,
                0.0,
                "Readability edit",
                result
            )

            self.refresh_history()

            self.humanizer_status.configure(
                text="Writing improved successfully!",
                text_color="#168653"
            )

        except tk.TclError:
            pass

        except Exception as error:
            messagebox.showerror(
                "Humanizer Error",
                str(error)
            )

        finally:
            self.finish_humanizer()

    def humanizer_error(self, error, request_id):

        if request_id != self.humanizer_request_id:
            return

        try:

            if self.humanizer_status.winfo_exists():
                self.humanizer_status.configure(
                    text="Unable to improve writing.",
                    text_color="#DC3545"
                )

            messagebox.showerror(
                "Humanizer Error",
                error
            )

        except tk.TclError:
            pass

        finally:
            self.finish_humanizer()

    def finish_humanizer(self):

        self.humanizer_busy = False

        try:

            if self.improve_button.winfo_exists():
                self.improve_button.configure(
                    state="normal",
                    text="Improve Writing"
                )

        except tk.TclError:
            pass

    # ----------------------------------
    # COPY IMPROVED TEXT
    # ----------------------------------

    def copy_rewritten_text(self):

        text = self.rewritten_text.get(
            "1.0", "end"
        ).strip()

        if not text:
            messagebox.showwarning(
                "Nothing to Copy",
                "Please improve some text first."
            )
            return

        try:

            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

            messagebox.showinfo(
                "Copied",
                "Improved text copied successfully!"
            )

        except Exception as error:

            messagebox.showerror(
                "Copy Error",
                str(error)
            )

    # ----------------------------------
    # UNDO
    # ----------------------------------

    def undo_input(self):

        try:
            self.original_text._textbox.edit_undo()
            self.update_writing_statistics()

        except tk.TclError:
            messagebox.showinfo(
                "Undo",
                "There is nothing to undo."
            )

    # ----------------------------------
    # REDO
    # ----------------------------------

    def redo_input(self):

        try:
            self.original_text._textbox.edit_redo()
            self.update_writing_statistics()

        except tk.TclError:
            messagebox.showinfo(
                "Redo",
                "There is nothing to redo."
            )

    # ----------------------------------
    # CLEAR ALL HUMANIZER TEXT
    # ----------------------------------

    def clear_humanizer(self):

        self.original_text.delete("1.0", "end")
        self.rewritten_text.delete("1.0", "end")

        self.original_text._textbox.edit_reset()
        self.rewritten_text._textbox.edit_reset()

        self.update_writing_statistics()

    # ----------------------------------
    # HISTORY TABLE STYLE
    # ----------------------------------

    def configure_table_style(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#24344D",
            fieldbackground="#FFFFFF",
            rowheight=32,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#EAF1FC",
            foreground="#172B4D",
            font=("Arial", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#D8E8FF")],
            foreground=[("selected", "#172B4D")]
        )

    # ----------------------------------
    # HISTORY
    # ----------------------------------

    def show_history(self):

        self.clear_content()
        self.update_navigation("History")

        self.create_page_header(
            "Analysis History",
            "View and manage your previous analyses and writing edits."
        )

        card = self.create_card(self.content)
        card.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        columns = (
            "ID", "Date", "Prediction",
            "AI Probability", "Text"
        )

        self.history_table = ttk.Treeview(
            card,
            columns=columns,
            show="headings"
        )

        for column in columns:
            self.history_table.heading(column, text=column)

        self.history_table.column("ID", width=45)
        self.history_table.column("Date", width=150)
        self.history_table.column("Prediction", width=130)
        self.history_table.column("AI Probability", width=120)
        self.history_table.column("Text", width=350)

        self.configure_table_style()

        self.history_table.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        button_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        button_frame.pack(
            anchor="w",
            padx=15,
            pady=10
        )

        ctk.CTkButton(
            button_frame,
            text="Refresh History",
            command=self.refresh_history
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Delete Selected",
            fg_color="#DC3545",
            hover_color="#B52B38",
            command=self.delete_selected
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Export CSV",
            fg_color="#1769E0",
            hover_color="#1257BC",
            command=self.export_history
        ).pack(side="left", padx=5)

        self.refresh_history()

    def refresh_history(self):

        table = getattr(self, "history_table", None)

        if table is None:
            return

        try:

            if not table.winfo_exists():
                return

        except tk.TclError:
            return

        for item in table.get_children():
            table.delete(item)

        for row in get_history():

            record_id, date, prediction, probability, preview = row

            score = (
                "—" if str(prediction).lower() == "readability edit"
                else f"{probability * 100:.1f}%"
            )

            table.insert(
                "",
                "end",
                values=(
                    record_id,
                    date,
                    prediction,
                    score,
                    preview
                )
            )

    # ----------------------------------
    # DELETE HISTORY
    # ----------------------------------

    def delete_selected(self):

        selected = self.history_table.selection()

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Please select a record first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete the selected record(s)?"
        )

        if not confirm:
            return

        for item in selected:

            values = self.history_table.item(
                item, "values"
            )

            delete_history_item(int(values[0]))

        self.refresh_history()

    # ----------------------------------
    # EXPORT HISTORY TO CSV
    # ----------------------------------

    def export_history(self):

        records = get_history()

        if not records:
            messagebox.showinfo(
                "No Data",
                "There is no analysis history to export."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="humantext_history.csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "ID",
                    "Date",
                    "Prediction",
                    "AI Probability",
                    "Text Preview"
                ])

                for row in records:

                    record_id, date, prediction, probability, preview = row

                    score = (
                        ""
                        if str(prediction).lower() == "readability edit"
                        else f"{float(probability) * 100:.1f}%"
                    )

                    writer.writerow([
                        record_id,
                        date,
                        prediction,
                        score,
                        preview
                    ])

            messagebox.showinfo(
                "Export Successful",
                "Your analysis history has been exported successfully."
            )

        except (OSError, ValueError, TypeError) as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )

    # ----------------------------------
    # MODEL PERFORMANCE
    # ----------------------------------

    def show_performance(self):

        self.clear_content()
        self.update_navigation("Model Performance")

        self.create_page_header(
            "Model Performance",
            "Evaluation statistics for your machine learning model."
        )

        metrics = getattr(self.detector, "metrics", {})

        cards_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        cards_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        for column in range(4):
            cards_frame.grid_columnconfigure(column, weight=1)

        results = [
            ("Accuracy", metrics.get("accuracy", 0)),
            ("Precision", metrics.get("precision", 0)),
            ("Recall", metrics.get("recall", 0)),
            ("F1 Score", metrics.get("f1_score", 0))
        ]

        for index, (name, value) in enumerate(results):

            card = self.create_card(cards_frame)
            card.grid(
                row=0,
                column=index,
                padx=7,
                pady=10,
                sticky="nsew"
            )

            ctk.CTkLabel(
                card,
                text=name,
                font=("Arial", 13),
                text_color="#8492A6"
            ).pack(pady=(20, 8))

            ctk.CTkLabel(
                card,
                text=f"{value * 100:.1f}%",
                font=("Arial", 24, "bold"),
                text_color="#1769E0"
            ).pack(pady=(0, 20))

        details = self.create_card(self.content)
        details.pack(
            fill="x",
            padx=30,
            pady=15
        )

        ctk.CTkLabel(
            details,
            text=(
                f"Training Samples: "
                f"{getattr(self.detector, 'training_count', 0)}"
            ),
            font=("Arial", 14),
            text_color="#172B4D"
        ).pack(anchor="w", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            details,
            text=(
                f"Testing Samples: "
                f"{metrics.get('test_samples', 0)}"
            ),
            font=("Arial", 14),
            text_color="#172B4D"
        ).pack(anchor="w", padx=20, pady=8)

        ctk.CTkLabel(
            details,
            text=self.model_status,
            font=("Arial", 13),
            text_color="#1769E0"
        ).pack(anchor="w", padx=20, pady=8)

        ctk.CTkLabel(
            details,
            text=(
                "Important: These metrics are based on a very small "
                "demonstration dataset. They are not reliable evidence "
                "of real-world AI authorship detection."
            ),
            font=("Arial", 11),
            text_color="#8492A6",
            wraplength=750,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(10, 20))


# ----------------------------------
# RUN APPLICATION
# ----------------------------------

if __name__ == "__main__":

    root = ctk.CTk()
    app = HumanTextApp(root)
    root.mainloop()