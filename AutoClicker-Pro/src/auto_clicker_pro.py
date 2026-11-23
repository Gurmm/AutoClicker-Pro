"""Windows 10/11 auto clicker. Requires pynput. Run: py auto_clicker_pro.py"""
import threading
import time
import math
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from pynput import mouse, keyboard

BG='#10151e'; PANEL='#1c2634'; FG='#f0f4fb'; MUTED='#aab8c9'; BLUE='#4778ed'

class App:
    def __init__(self, root):
        self.root=root; root.title('AutoClicker Pro｜定點與雙點點擊'); root.geometry('580x810'); root.configure(bg=BG)
        self.lock=threading.RLock(); self.stop_event=threading.Event(); self.closed=False; self.running=False
        self.points={'A':None,'B':None}; self.last=None; self.clicks=0; self.rounds=0; self.status='待機'; self.remaining='--'
        self.mode=tk.StringVar(value='single'); self.interval=tk.StringVar(value='600'); self.a_count=tk.StringVar(value='1'); self.b_count=tk.StringVar(value='1'); self.click_gap=tk.StringVar(value='1'); self.move_duration=tk.StringVar(value='1'); self.loops=tk.StringVar(value='0')
        self.always_on_top=tk.BooleanVar(value=False)
        self._time_entries={}; self._time_error=None; self.load_preferences(); self.make_ui()
        self.apply_always_on_top()
        self.kl=keyboard.Listener(on_press=self.on_key); self.kl.start()
        for v in (self.mode,self.interval,self.a_count,self.b_count,self.click_gap,self.move_duration,self.loops,self.always_on_top):
            v.trace_add('write',lambda *_: self.schedule_save())
        root.protocol('WM_DELETE_WINDOW',self.close); self.refresh()

    @staticmethod
    def preferences_path():
        base = Path(os.environ.get('APPDATA') or Path.home())
        return base / 'AutoClicker_Pro' / 'settings.json'

    def load_preferences(self):
        """Load prior numeric settings, not cursor coordinates or running state."""
        try:
            data=json.loads(self.preferences_path().read_text(encoding='utf-8'))
            if not isinstance(data,dict):return
            mode=data.get('mode','single')
            if mode not in ('single','dual'):return
            def dec(key,default,minimum,maximum):
                val=str(data.get(key,default))
                number=self.decimal_number(val)
                return val if math.isfinite(number) and minimum<=number<=maximum else default
            cycle=dec('interval','600',0.01,86400*365)
            limit=self.decimal_number(cycle)
            self.mode.set(mode)
            self.always_on_top.set(data.get('always_on_top',False) is True)
            self.interval.set(cycle)
            self.click_gap.set(dec('click_gap','1',0,min(limit,86400)))
            self.move_duration.set(dec('move_duration','1',0,min(limit,3600)))
            for key,var,default,maxnum in [('a_count',self.a_count,'1',100000),('b_count',self.b_count,'1',100000),('loops',self.loops,'0',1000000)]:
                raw=str(data.get(key,default))
                var.set(raw if raw.isascii() and raw.isdecimal() and int(raw)<=maxnum else default)
            if (mode=='single' and int(self.a_count.get())==0) or (mode=='dual' and int(self.a_count.get())+int(self.b_count.get())==0):
                self.a_count.set('1')
        except (OSError,ValueError,TypeError,OverflowError):
            pass  # Corrupt/missing preferences should not prevent startup.

    def schedule_save(self):
        if getattr(self,'closed',False):return
        if getattr(self,'_save_after',None) is not None:
            self.root.after_cancel(self._save_after)
        self._save_after=self.root.after(650,self.save_preferences)

    def save_preferences(self):
        self._save_after=None
        try:
            cycle=self.decimal_number(self.interval.get())
            gap=self.decimal_number(self.click_gap.get())
            move=self.decimal_number(self.move_duration.get())
            a=int(self.a_count.get());b=int(self.b_count.get());loops=int(self.loops.get())
            mode=self.mode.get()
            if not (math.isfinite(cycle) and 0.01<=cycle<=86400*365
                    and math.isfinite(gap) and 0<=gap<=min(cycle,86400)
                    and math.isfinite(move) and 0<=move<=min(cycle,3600)
                    and 0<=a<=100000 and 0<=b<=100000 and 0<=loops<=1000000
                    and mode in ('single','dual')
                    and (a>0 if mode=='single' else a+b>0)):
                return
            data={'mode':mode,'interval':self.interval.get(),
                  'click_gap':self.click_gap.get(),'move_duration':self.move_duration.get(),
                  'a_count':self.a_count.get(),'b_count':self.b_count.get(),
                  'loops':self.loops.get(),'always_on_top':self.always_on_top.get()}
            path=self.preferences_path();path.parent.mkdir(parents=True,exist_ok=True)
            temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(temp,path)
        except (OSError,ValueError,TypeError,OverflowError):
            pass

    def label(self,parent,text,size=10,color=FG,**kw):
        return tk.Label(parent,text=text,font=('Segoe UI',size),fg=color,bg=parent.cget('bg'),**kw)
    def make_ui(self):
        outer=tk.Frame(self.root,bg=BG,padx=20,pady=15);outer.pack(fill='both',expand=True)
        self.label(outer,'滑鼠自動點擊器 Pro',19).pack(anchor='w')
        self.label(outer,'定點點擊 / A → B 雙點移動點擊',10,MUTED).pack(anchor='w',pady=(2,8))
        pinbar=tk.Frame(outer,bg=BG);pinbar.pack(fill='x',pady=(0,10))
        self.pin_btn=tk.Button(pinbar,text='📌 固定在最上層：關',command=self.toggle_always_on_top,
            bg='#304054',fg=FG,activebackground=BLUE,activeforeground='white',
            relief='flat',font=('Segoe UI',10),pady=7)
        self.pin_btn.pack(side='left',fill='x',expand=True)
        self.label(pinbar,'可隨時切換',9,MUTED).pack(side='right',padx=(10,0))
        panel=tk.Frame(outer,bg=PANEL,padx=14,pady=12);panel.pack(fill='x')
        self.coord_label=self.label(panel,'A：尚未記錄     B：尚未記錄',12);self.coord_label.pack(anchor='w')
        self.state_label=self.label(panel,'狀態：待機',11);self.state_label.pack(anchor='w',pady=(10,3))
        self.info_label=self.label(panel,'下次動作：--     點擊：0 次     輪數：0',10,MUTED);self.info_label.pack(anchor='w')
        mode_frame=tk.Frame(outer,bg=BG);mode_frame.pack(fill='x',pady=(12,6))
        self.label(mode_frame,'操作模式',11).pack(anchor='w')
        for text,value in [('單點 A（每隔固定秒數點擊）','single'),('雙點 A → B（A、B 次數獨立設定）','dual')]:
            tk.Radiobutton(mode_frame,text=text,variable=self.mode,value=value,bg=BG,fg=FG,selectcolor=PANEL,activebackground=BG,activeforeground=FG,font=('Segoe UI',10)).pack(anchor='w')
        config=tk.Frame(outer,bg=PANEL,padx=14,pady=10);config.pack(fill='x',pady=(4,10))
        fields=[('每輪等待時間（秒）',self.interval),('A 點點擊次數（可為 0）',self.a_count),('B 點點擊次數（可為 0）',self.b_count),('同一位置點擊間隔（秒）',self.click_gap),('A → B 移動時間（秒）',self.move_duration),('循環輪數（0 = 無限）',self.loops)]
        for i,(name,var) in enumerate(fields):
            self.label(config,name,10).grid(row=i,column=0,sticky='w',pady=5)
            entry=tk.Entry(config,textvariable=var,width=15,font=('Segoe UI',11),bg='#304054',fg=FG,insertbackground=FG,relief='flat')
            entry.grid(row=i,column=1,sticky='e',padx=(16,0),pady=5,ipady=4)
            if var in (self.interval,self.click_gap,self.move_duration):
                self._time_entries[str(var)]=entry
                entry.bind('<KeyPress>',self.decimal_key,add='+')
                entry.bind('<FocusOut>',lambda event, v=var: self.on_time_focus_out(v),add='+')
        config.columnconfigure(0,weight=1)
        self._time_error=self.label(outer,'',9,'#ff9292')
        self._time_error.pack(anchor='w')
        for v in (self.interval,self.click_gap,self.move_duration):
            v.trace_add('write',lambda *_:self.validate_time_live())
        self.validate_time_live()
        self.label(outer,'座標鎖定：只有 F7 / F9 會改變座標',10,MUTED).pack(anchor='w',pady=(2,8))
        buttons=tk.Frame(outer,bg=BG);buttons.pack(fill='x')
        for i,(text,cmd) in enumerate([('記錄 A 說明（F7）',lambda:self.show_record_help('A')),('記錄 B 說明（F9）',lambda:self.show_record_help('B'))]):
            tk.Button(buttons,text=text,command=cmd,bg='#304054',fg=FG,relief='flat',font=('Segoe UI',10),pady=8).grid(row=0,column=i,sticky='ew',padx=3)
        buttons.columnconfigure(0,weight=1);buttons.columnconfigure(1,weight=1)
        actions=tk.Frame(outer,bg=BG);actions.pack(fill='x',pady=(10,5))
        self.toggle_btn=tk.Button(actions,text='▶ 開始（F6）',command=self.toggle,bg=BLUE,fg='white',relief='flat',font=('Segoe UI',11,'bold'),pady=9);self.toggle_btn.grid(row=0,column=0,sticky='ew',padx=3)
        tk.Button(actions,text='■ 結束（F8）',command=self.close,bg='#304054',fg=FG,relief='flat',font=('Segoe UI',11),pady=9).grid(row=0,column=1,sticky='ew',padx=3)
        actions.columnconfigure(0,weight=1);actions.columnconfigure(1,weight=1)
        self.label(outer,'A、B 可各自設定 0 次（只移動不點擊）；雙點總次數為 A+B。',9,MUTED).pack(anchor='w',pady=(8,0))
        self.label(outer,'座標記錄完成後已鎖定；任意手動或自動點擊均不會更新。',9,MUTED).pack(anchor='w')
        self.label(outer,'設定自動儲存；重新開啟會載入上次參數（不保存座標）。',9,MUTED).pack(anchor='w')
        self.label(outer,'移至主螢幕左上角 (0,0) 可緊急停止。',9,MUTED).pack(anchor='w')

    def apply_always_on_top(self):
        """Keep the window above normal windows without changing click coordinates."""
        enabled=bool(self.always_on_top.get())
        self.root.attributes('-topmost',enabled)
        if hasattr(self,'pin_btn'):
            self.pin_btn.config(text='📌 固定在最上層：開' if enabled else '📌 固定在最上層：關',
                                bg=BLUE if enabled else '#304054')

    def toggle_always_on_top(self):
        self.always_on_top.set(not self.always_on_top.get())
        self.apply_always_on_top()
        self.save_preferences()

    def decimal_key(self,event):
        """Keep the decimal separator visible, including numpad and CJK punctuation."""
        char = event.char
        # Some Windows layouts emit no character for the keypad decimal key.
        if event.keysym in ('KP_Decimal', 'KP_Separator'):
            char = '.'
        elif char not in ('.', '．', '。', ',', '，', '｡'):
            return
        widget = event.widget
        # Replace selection if any; do not overwrite a previously entered dot.
        try:
            start, end = widget.index(tk.SEL_FIRST), widget.index(tk.SEL_LAST)
            widget.delete(start, end)
            widget.icursor(start)
        except tk.TclError:
            pass
        if '.' not in widget.get():
            widget.insert(tk.INSERT, '.')
        return 'break'

    @staticmethod
    def decimal_number(value):
        value = value.strip().translate(str.maketrans('０１２３４５６７８９．。｡－＋，', '0123456789...-+,'))
        return float(value.replace(',', '.'))

    def normalize_decimal_display(self, var):
        """Only normalize punctuation on leaving a field; preserve user decimals."""
        value = var.get().strip().translate(str.maketrans('０１２３４５６７８９．。｡－＋，', '0123456789...-+,'))
        value = value.replace(',', '.')
        if value != var.get():
            var.set(value)

    def validate_time_live(self):
        """Warn while typing, without modifying incomplete decimals such as 0. or .5."""
        try:
            limit=self.decimal_number(self.interval.get())
            if not math.isfinite(limit) or limit<=0:
                raise ValueError
        except ValueError:
            self._time_error.config(text='請輸入有效的每輪等待時間')
            return
        exceeded=[]
        for label,var in [('同一位置點擊間隔',self.click_gap),('A → B 移動時間',self.move_duration)]:
            try:
                val=self.decimal_number(var.get())
                if math.isfinite(val) and val>limit:
                    exceeded.append(label)
            except ValueError:
                pass  # Allow intermediate typing states.
        self._time_error.config(text=('超過每輪等待時間：'+'、'.join(exceeded)) if exceeded else '')

    def on_time_focus_out(self,var):
        """Clamp only after editing; changing the cycle limit clamps both dependent fields."""
        self.normalize_decimal_display(var)
        try:
            limit=self.decimal_number(self.interval.get())
            if not math.isfinite(limit) or limit<=0:
                return
        except ValueError:
            return
        for field in (self.click_gap,self.move_duration):
            try:
                value=self.decimal_number(field.get())
            except ValueError:
                continue
            if math.isfinite(value) and value>limit:
                # Preserve the original decimal representation of the upper limit.
                field.set(self.interval.get())
        self.validate_time_live()

    def show_record_help(self,point):
        key='F7' if point=='A' else 'F9'
        messagebox.showinfo('記錄座標',f'請將滑鼠移到目標 {point} 點，直接按 {key} 記錄。\n\n一般滑鼠點擊不會改變任何座標。')
    def on_key(self,key):
        if self.closed:return False
        if key==keyboard.Key.f6:self.root.after(0,self.toggle)
        elif key==keyboard.Key.f7:self.root.after(0,lambda:self.record_cursor('A'))
        elif key==keyboard.Key.f9:self.root.after(0,lambda:self.record_cursor('B'))
        elif key==keyboard.Key.f8:self.root.after(0,self.close);return False
    def record_cursor(self,p):
        if self.running:return
        with self.lock:self.points[p]=mouse.Controller().position;self.last=p
        self.status=f'已記錄 {p} 點'
    def settings(self):
        try:
            interval=self.decimal_number(self.interval.get());gap=self.decimal_number(self.click_gap.get());duration=self.decimal_number(self.move_duration.get());a_count=int(self.a_count.get());b_count=int(self.b_count.get());loops=int(self.loops.get())
            if not(all(math.isfinite(x) for x in (interval,gap,duration)) and 0.01<=interval<=86400*365 and 0<=gap<=min(86400,interval) and 0<=duration<=min(3600,interval) and 0<=a_count<=100000 and 0<=b_count<=100000 and 0<=loops<=1000000 and (a_count>0 if self.mode.get()=='single' else a_count+b_count>0)):raise ValueError
            return interval,gap,duration,a_count,b_count,loops,self.mode.get()
        except ValueError:
            messagebox.showerror('設定錯誤','請輸入有效數值：輪間隔 ≥ 0.01 秒；點擊間隔及 A→B 移動時間不得大於每輪等待時間；A/B 點擊次數可為 0，但雙點模式不能同時為 0。');return None
    def toggle(self):
        if self.closed:return
        if self.running:
            self.stop_event.set();self.running=False;self.status='已暫停';self.remaining='--';return
        opts=self.settings()
        if opts is None:return
        self.save_preferences()
        if not self.points['A'] or (opts[-1]=='dual' and not self.points['B']):
            messagebox.showwarning('缺少座標','請先記錄 A 點'+('與 B 點' if opts[-1]=='dual' else ''));return
        self.stop_event=threading.Event();self.running=True;self.status='運行中';self.clicks=0;self.rounds=0
        points=dict(self.points);threading.Thread(target=self.worker,args=(opts,points,self.stop_event),daemon=True).start()
    def wait(self,secs,event):
        deadline=time.monotonic()+secs
        while not event.is_set():
            remain=deadline-time.monotonic();self.remaining=f'{max(0,remain):.1f} 秒'
            if remain<=0:return True
            event.wait(min(0.1,remain))
        return False
    def move(self,controller,dest,duration,event):
        start=controller.position
        if duration==0:
            controller.position=dest;return not event.is_set()
        began=time.monotonic()
        while not event.is_set():
            t=min(1,(time.monotonic()-began)/duration)
            controller.position=(round(start[0]+(dest[0]-start[0])*t),round(start[1]+(dest[1]-start[1])*t))
            if t>=1:return True
            event.wait(0.015)
        return False
    def worker(self,opts,points,event):
        interval,gap,duration,a_count,b_count,loops,mode=opts;ctl=mouse.Controller()
        try:
            while not event.is_set() and (loops==0 or self.rounds<loops):
                self.status='等待下一輪';
                if not self.wait(interval,event):break
                sequence=['A'] if mode=='single' else ['A','B']
                for index,p in enumerate(sequence):
                    if event.is_set():break
                    self.status=f'移動至 {p} 點'
                    if not self.move(ctl,points[p],duration if index>0 else 0,event):break
                    count=a_count if p=='A' else b_count
                    for n in range(count):
                        if event.is_set():break
                        # Stop immediately if cursor has been moved to upper-left corner.
                        if ctl.position[0]<=1 and ctl.position[1]<=1:
                            event.set();self.status='緊急停止';break
                        ctl.click(mouse.Button.left,1);self.clicks+=1
                        self.status=f'{p} 點：{n+1}/{count}'
                        if n<count-1 and not self.wait(gap,event):break
                if event.is_set():break
                self.rounds+=1
            if not event.is_set():self.status='已完成' if loops else '已停止'
        except Exception as exc:
            self.status=f'錯誤：{exc}'
        finally:
            self.running=False;self.remaining='--';event.set()
    def refresh(self):
        if self.closed:return
        a=self.points['A'];b=self.points['B']
        fmt=lambda p: f'({p[0]}, {p[1]})' if p else '尚未記錄'
        self.coord_label.config(text=f'A：{fmt(a)}     B：{fmt(b)}')
        self.state_label.config(text='狀態：'+self.status)
        self.info_label.config(text=f'倒數：{self.remaining}     點擊：{self.clicks} 次     輪數：{self.rounds}')
        self.toggle_btn.config(text='Ⅱ 暫停（F6）' if self.running else '▶ 開始（F6）')
        self.root.after(100,self.refresh)
    def close(self):
        if self.closed:return
        if getattr(self,'_save_after',None) is not None:
            self.root.after_cancel(self._save_after)
        self.save_preferences()
        self.closed=True;self.stop_event.set();self.running=False
        self.kl.stop();self.root.destroy()

if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
