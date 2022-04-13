#Note i used some new files (namely larger scroll and silence voice), you will
#need to inlcude these files from github before compile the code. These files are
#based on my preference, of course, feel free to use them or your own.
# sound/0_6s-silence.ogg
# efe/scroll_new.png
# efe/scroll_thumb_new.png

#############################

style vscrollbar is bar:
    xsize 40
    ysize 540
    xanchor 0.5
    yanchor 0.5
    top_bar "efe/scroll_new.png"
    bottom_bar "efe/scroll_new.png"
    thumb im.Scale("efe/scroll_thumb_new.png", 42, 78)

init -3 python:


    style.readback_window.xmaximum = config.screen_width
    style.readback_window.ymaximum = config.screen_height


    style.readback_frame.background = None
    style.readback_frame.xpadding = 110
    style.readback_frame.ypadding = 0




    style.readback_text.color = "#fff"

    style.create("readback_button", "readback_text")
    style.readback_button.background = None

    style.create("readback_button_text", "readback_text")
    style.readback_button_text.idle_color = "#cc4"
    style.readback_button_text.selected_color = "#f12"
    style.readback_button_text.hover_color = "#f12"

    style.readback_label_text.bold = True


    config.locked = False


    config.readback_buffer_length = 150
    config.readback_full = True
    config.readback_disallowed_tags = ["size"]
    config.readback_choice_prefix = "<< "
    config.readback_choice_postfix = " >>"
    config.readback_space_after_nvl_clear = True
    config.readback_nvl_page = False




    config.locked = True

init -2 python:


    class ReadbackADVCharacter(ADVCharacter):
        def do_done(self, who, what):
            store_say(who, what)
            store.current_voice = ''
            super(ReadbackADVCharacter, self).do_done(who, what)
            return

        def do_extend(self):
            delete_last_line()
            super(ReadbackADVCharacter, self).do_extend()
            return

    class ReadbackNVLCharacter(NVLCharacter):
        def do_done(self, who, what):
            store_say(who, what)
            store.current_voice = ''
            super(ReadbackNVLCharacter, self).do_done(who, what)
            return

        def do_extend(self):
            delete_last_line()
            super(ReadbackNVLCharacter, self).do_extend()
            return

    class TrackMultipleVoices:   # added class to store multple voices if found in a single sentence
        def __init__(self):
            self.buffer = []
            self.update_buffer = False
            self.previous_voice_hist = None

        def updateStatus(self, previous_voice_hist):
            self.update_buffer = True
            self.previous_voice_hist = previous_voice_hist

        def getStatus(self):
            return self.update_buffer

        def updateBuffer(self, current_voice):
            if self.update_buffer:
                if isinstance(self.previous_voice_hist, list):
                    for element in self.previous_voice_hist:
                        self.buffer.append(element)

                else:
                    self.buffer.append(self.previous_voice_hist)

                self.buffer.append(current_voice)
                self.CheckEmptyBuffer()
                self.update_buffer = False

        def emptyBuffer(self):
            self.buffer = []

        def fetchBuffer(self):
            return self.buffer

        def CheckEmptyBuffer(self):
            if (not any(self.buffer)):
                self.buffer = []




    adv = ReadbackADVCharacter()
    nvl = ReadbackNVLCharacter()
    NVLCharacter = ReadbackNVLCharacter
    buffer_voices = TrackMultipleVoices()


    # rewriting voice function to replay voice files when you clicked dialogues in text history screen
    def voice(file, **kwargs):
        if not config.has_voice:
            return

        _voice.play = file

        store.current_voice = file

    def inject_silenct_voices(list_files, silence_audio = "sound/0_6s-silence.ogg"):
        new_audio_list = []
        for file_ in list_files[0:-1]:
            new_audio_list.append(file_)
            new_audio_list.append(silence_audio)

        new_audio_list.append(list_files[-1])
        return new_audio_list




    def menu(items, **add_input):
        rv = renpy.display_menu(items, **add_input)


        for label, val in items:
            if rv == val:
                store.current_voice = ''
                store_say(None, config.readback_choice_prefix + label)
        return rv


    builtin_nvl_menu = nvl_menu
    def nvl_menu(items):
        rv = builtin_nvl_menu(items)
        for label, val in items:
            if rv == val:
                store.current_voice = ''
                store_say(None, config.readback_choice_prefix + label)
        return rv

    builtin_nvl_clear = nvl_clear
    def nvl_clear():
        builtin_nvl_clear()
        if config.readback_nvl_page:
            readback_buffer.append([])
        elif config.readback_space_after_nvl_clear:
            readback_buffer.append((None, "",''))

    def readback_reset():
        global readback_buffer
        if config.readback_nvl_page:
            readback_buffer = [ [] ]
        else:
            readback_buffer = [ ]

    config.start_callbacks.append(readback_reset)
    current_voice = None

    def store_say(who, what):
        global readback_buffer, current_voice

        if buffer_voices.getStatus():
            buffer_voices.updateBuffer(current_voice)
            new_line = (preparse_say_for_store(who), preparse_say_for_store(what), buffer_voices.fetchBuffer())
            buffer_voices.emptyBuffer()

        else:
            new_line = (preparse_say_for_store(who), preparse_say_for_store(what), current_voice)

        if config.readback_nvl_page:
            readback_buffer[-1].append(new_line)
        else:
            readback_buffer.append(new_line)
        readback_prune()

    def delete_last_line():
        global readback_buffer
        if config.readback_nvl_page:
            buffer_voices.updateStatus(readback_buffer[-1][-1][2])
            del readback_buffer[-1][-1]
        else:
            buffer_voices.updateStatus(readback_buffer[-1][2])
            del readback_buffer[-1]


    disallowed_tags_regexp = ""
    for tag in config.readback_disallowed_tags:
        if disallowed_tags_regexp != "":
            disallowed_tags_regexp += "|"
        disallowed_tags_regexp += "{"+tag+"=.*?}|{"+tag+"}|{/"+tag+"}"

    import re
    readback_remove_tags_expr = re.compile(disallowed_tags_regexp)
    def preparse_say_for_store(input):
        global readback_remove_tags_expr
        if input:
            return re.sub(readback_remove_tags_expr, "", input)

    def readback_prune():
        global readback_buffer
        while len(readback_buffer) > config.readback_buffer_length:
            del readback_buffer[0]


    def readback_catcher():
        ui.add(renpy.Keymap(rollback=(SetVariable("readback_yvalue", 1.0), ShowMenu("text_history"))))
        ui.add(renpy.Keymap(rollforward=ui.returns(None)))


    if config.readback_full:
        config.rollback_enabled = False
        config.rollback_enabled = True
        config.overlay_functions.append(readback_catcher)


init python:
    readback_yvalue = 1.0



    class ReadbackAdj(ui.adjustment):
        def change(self,value):
            if value > self._range and self._value == self._range:
                return Return()
            else:
                return ui.adjustment.change(self, value)

    def readback_store_yvalue(y):
        global readback_yvalue
        readback_yvalue = int(y)


    def readback_change_page(y):
        global readback_yvalue
        readback_yvalue = int(y)
        renpy.restart_interaction()

    def readback_paged_max():
        max = len(readback_buffer) - 1
        if max > 0 and len(readback_buffer[max]) == 0:
            max = max - 1
        return max

    def readback_fix_yvalue():
        global readback_yvalue
        if not isinstance(readback_yvalue, int):
            readback_yvalue = readback_paged_max()

    def readback_show_prev_page():
        global readback_yvalue
        if (readback_yvalue > 0):
            readback_yvalue -= 1
            renpy.restart_interaction()

    def readback_show_next_page():
        global readback_yvalue
        if (readback_yvalue < readback_paged_max()):
            readback_yvalue += 1
            renpy.restart_interaction()
        else:
            return True


screen text_history:
    tag menu


    if config.readback_nvl_page:
        $ readback_fix_yvalue()

        window:
            style_group "readback"

            frame:
                yfill True
                has vbox

                key "rollback" action readback_show_prev_page
                key "rollforward" action readback_show_next_page

                null height 10

                for line in readback_buffer[readback_yvalue]:

                    if line[0]:
                        label line[0]

                    if not line[2]:
                        text line[1]

                    else:
                        if isinstance(line[2], list):
                            #if multiple voices found in a sentence, play them one after another
                            $ new_list = inject_silenct_voices(line[2])  #inject silence audio between voices
                            textbutton line[1] action Play("voice", [element for element in new_list])



                        else:
                            textbutton line[1] action Play("voice", line[2])

                    null height 10

            textbutton _("Exit") action Return() align (.97, 1.0)

    else:
        $ adj = ReadbackAdj(changed = readback_store_yvalue, step = 220)

        window:
            id "readback"
            style_group "readback"

            side "c r":

                frame:
                    has viewport:
                        mousewheel True
                        draggable True
                        yinitial readback_yvalue
                        yadjustment adj

                    vbox:
                        null height 10

                        for line in readback_buffer:

                            if line[0]:
                                label line[0]

                            if not line[2]:
                                text line[1]

                            else:
                                if isinstance(line[2], list):
                                    #if multiple voices found in a sentence, play them one after another
                                    $ new_list = inject_silenct_voices(line[2])  #inject silence audio between voices
                                    textbutton line[1] action Play("voice", [element for element in new_list])

                                else:
                                    textbutton line[1] action Play("voice", line[2])

                            null height 10

                vbar adjustment adj style 'vscrollbar' xpos -37 ypos 370 #modified to match the new scroll

            textbutton _("Exit") action Return() align (.97, 1.0)


    add "efe/obi.png" alpha 0.5
    add "efe/caption_log.png" xpos 40
# Decompiled by unrpyc: https://github.com/CensoredUsername/unrpyc
