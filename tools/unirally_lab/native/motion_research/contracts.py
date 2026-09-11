"""Isolated arithmetic contracts recovered for R-0011-motion.

Address-keyed dictionaries here are captured call arguments, NOT a runtime or a
persistent native state design. Unsupported behavior stays in the original.
All words wrap modulo 65536; signed comparisons follow the original N bit.
"""
from math import isqrt


def signed(value):
    value &= 65535
    return value - 65536 if value & 32768 else value


def jump_update(state, inhibit):
    """$82:A8C9..A96E; caller invokes only on the rider's active phase."""
    s = dict(state)
    if inhibit or s[0xf41] or s[0xf5d] or s[0xf31] & 128:
        return s
    advance = bool(s[0xf93])
    if not advance and s[0xf91]:
        if s[0xf2b]:
            s[0xfa5] = s[0xf1f]
            return s
        s[0xf91] = 0
        advance = True
    if not advance:
        if not s[0xfa5] and s[0xf1f] and signed(s[0xf33]-2) < 0:
            s[0xf91] = 1
    elif not s[0xf1f]:
        s[0xf93] = 0
    else:
        s[0xf93] = (s[0xf93]+1) & 65535
        if signed(s[0xf93]-9) >= 0:
            s[0xf93] = 0
        else:
            impulse = (s[0xf95] + (-144 if signed(s[0xf93]-5)<0 else -192)) & 65535
            if signed(s[0xfab]-impulse) >= 0:
                s[0xfab] = impulse
    s[0xfa5] = s[0xf1f]
    return s


def pose_update(state, square_table, slope_table):
    """$83:ED7B..F0FA, using captured arguments and two identity-checked tables.

    The orientation state is a 64-step circle. Animation phase is modulo24.
    Unknown mode switches deliberately retain their WRAM addresses here.
    """
    s = dict(state)
    steering = 0
    if not s[0xf2b]:
        extra, table_group = 0, 0
        if s[0xf31] & 128:
            base, table_group = 0, 64
        elif s[0xf15] and s[0xf4d]:
            extra = signed(s[0xf17]); base = 23 if s[0xf51] else -23
        else:
            if not s[0xe7b]:
                base = signed(s[0xf5f]) >> 5
            elif s[0xf2d]:
                base = signed(s[0xfa9]) >> 1
            else:
                base = signed(s[0xf3f] or s[0xfa9]) >> 5
        target = signed((s[0xf25] if s[0xf23] else extra) + base)
        target = max(-31, min(31, target))
        index = (target if target >= 0 else -target+32) + table_group
        s[0xfa3] = slope_table[index]
    target = s[0xfa3]
    orientation = (s[0xf53]+s[0xf57]) & 65535
    if s[0xf55]:
        orientation += s[0xf55]
    elif signed(s[0xf33]-9) < 0:
        if target == s[0xf53]:
            orientation = s[0xf53]
        else:
            if signed(target-32) >= 0:
                increase = 1 <= signed(target-s[0xf53]) <= 32
            else:
                increase = not (1 <= signed(s[0xf53]-target) <= 32)
            direction = 1 if increase else -1
            orientation = s[0xf53]+direction
            if signed(s[0xf73]-16)>=0:
                for _ in range(2):
                    if (orientation & 63) == target:break
                    orientation = (orientation & 63)+direction
    s[0xf53] = orientation & 63
    wobble = abs(signed(s[0xf37]))//16
    if signed(s[0xf37])<0:wobble=-wobble
    s[0xf81] = (s[0xf53]+wobble+(signed(s[0xfad])>>1)) & 63
    if not s[0x4c7]&1 and s[0xfad]:
        s[0xfad] = (signed(s[0xfad])+(-1 if signed(s[0xfad])>=0 else 1)) & 65535
    if s[0xf81] and s[0xf51]:s[0xf81]=64-s[0xf81]
    s[0xf71],s[0xf6f],s[0xf6d] = s[0xf6f],s[0xf6d],s[0xf73]
    if signed(s[0xf93]-1)>=0 or s[0xf2b]:
        steering = signed(s[0xf99])
        if s[0x4c7]&3 == 3:
            steering += -1 if steering>0 else (1 if steering<0 else 0)
        s[0xf99] = steering & 65535
    else:
        dx = signed(s[0xf9b]-s[0xa5]); dy = signed(s[0xf9d]-s[0xa7])
        if abs(dy)<3:dy=0
        distance = isqrt((square_table[abs(dx)&255]+square_table[abs(dy)&255]) & 65535)
        if dx<0:distance=-distance
        s[0xf73]=distance & 65535
        accumulation=signed(s[0xf9f]+distance)
        quotient,remainder=divmod(abs(accumulation),3)
        if accumulation<0:quotient=-quotient
        if dx<0:remainder=-remainder
        s[0xf9f]=remainder & 65535
        steering=quotient
        s[0xf99]=steering & 65535
    if s[0xf51]:steering=-steering
    if s[0xf3d]:steering=signed(s[0xf3d])
    s[0xf8d]=signed(s[0xf8d]+steering)%24
    animation=None
    if s[0xf15]&255:
        rate=abs(signed(s[0xf99]))
        if rate<3 and s[0xf4d]&255:s[0xf4d]=(s[0xf4d]-1)&255
        elif rate>=5 and (s[0xf4d]&255)!=2:s[0xf4d]=(s[0xf4d]+1)&255
        if s[0xf4d]&255:
            frame=s[0xfe3]+(s[0xf8d]&1)+s[0x300]
            if signed(frame-3)>=0:frame-=3
            s[0xfe3]=frame&65535
            animation=frame*64+(0x8e0 if s[0xf4d]&255==1 else 0x820)
    if animation is None:animation=s[0xf8d]*64
    pose=(animation+s[0xf81])&65535
    s[0xf73]=abs(signed(s[0xf73]))&65535
    s[0xf9b],s[0xf9d]=s[0xa5],s[0xa7]
    s[0xfa1]=s[0xf59] or pose
    return s


def integrate_position(state):
    """$82:A627..A6F7 after the speed clamp; residues are signed /32 units."""
    s=dict(state);rider=s[0xff9]
    for coordinate,velocity,residue in [(0xa5,0xfa9,0x401+rider),(0xa7,0xfab,0x405+rider)]:
        total=signed(s[velocity]+s[residue])
        whole,remainder=divmod(abs(total),32)
        if total<0:whole,remainder=-whole,-remainder
        s[coordinate]=(s[coordinate]+whole)&65535
        s[residue]=remainder&65535
        if coordinate==0xa5:s[coordinate]&=s[0xd4f]
    if s[0xf17] and not s[0xf2d] and signed(s[0xf33]-2)<0 and not s[0xf31]&128:
        extra=-1 if signed(s[0xfab])<0 else (1 if s[0xf23] else 4)
        s[0xa7]=(s[0xa7]+extra)&65535
    return s


def gravity_update(state):
    """$82:A96F..A9B2; gravity and its separate +1 coordinate step."""
    s=dict(state)
    if s[0xf4b] or s[0x547+s[0xff9]] or signed(s[0xfab]-512)>=0:return s
    vertical=signed(s[0xfab])
    increment=16 if vertical<0 else 16-(vertical>>5)
    s[0xfab]=(vertical+increment+3)&65535
    s[0xa7]=(s[0xa7]+1)&65535
    return s


def rolling_mode(state):
    """$82:A288..A2DA: hysteresis selecting the alternate rolling animation."""
    s=dict(state)
    if s[0xf31]&128:s[0xf15]=1
    elif s[0xf33]==9 or s[0xf23] or signed(s[0xf81]-45)<0:s[0xf15]=0
    elif s[0xf15] and signed(s[0xf73]-14)<0:s[0xf15]=0
    elif not s[0xf15] and signed(s[0xf73]-16)<0:pass
    else:s[0xf15]=int((signed(s[0xfa9])>=0) if s[0xf51] else (signed(s[0xfa9])<0))
    return s


def rotation_input(state):
    """$82:A49F..A5F9, omitting audio-only publication."""
    s=dict(state)
    if (s[0xf1b] and s[0xf1d]) or (abs(signed(s[0xf17]))<30 and signed(s[0xf33]-9)<0) or s[0xf49]&255 or s[0xf89]&255:
        s[0xf57]=0
    elif s[0xf23]&255 or s[0xf5d]&255:pass
    elif s[0xf1d]&255:
        s[0xf57]=(s[0xf57]&0xff00)|((2-s[0x31d+s[0xff9]])&255)
    elif s[0xf1b]&255:
        s[0xf57]=(s[0xf57]&0xff00)|((-2+s[0x31d+s[0xff9]])&255)
    else:s[0xf57]=0
    return s


def opponent_inputs(state, feature_flag):
    """Observed primary $83:E082..E253 subset. Other AI modes reject explicitly."""
    s=dict(state)
    if not s[0xc6d] or s[0xc73] or s[0xb95] or s[0xfc7]&0xc000 or s[0x1275]!=1:
        raise ValueError('AI call outside recovered primary control domain')
    s[0x31b]=2;s[0x333]=0;s[0x32f]=0;s[0x32b]=0;s[0x327]=0;s[0x31f]=0
    if s[0xfc7]&0x2000:
        s[0x333]=1
        if s[0xc6f]:
            if s[0xc75]&1:s[0x32f]=1
            if s[0xc75]&6:raise ValueError('unsupported primary AI input continuation')
            return s
        if signed(s[0x54d]-4)<0 and feature_flag:
            if signed(s[0xfcd]-s[0xfcf]-3)>=0:raise ValueError('unsupported AI catch-up jump branch')
            s[0x333]=s[0x300]
        elif signed(s[0x54d]-4)>=0:
            s[0xc6f]=abs(signed(s[0x4c1]))>>1
            if feature_flag:raise ValueError('unsupported repeated AI jump choice')
            s[0x1277]=30
            if s[0xb70]:raise ValueError('unsupported nonflat AI initiation')
            if signed(s[0x4bd])<0:raise ValueError('unsupported reverse AI initiation')
            s[0x32f]=1;s[0xc75]=1
            return s
    else:s[0x333]=s[0x300]
    s[0xc75]=s[0xc6f]=0
    # The later recovery branch is absent in this domain: its predicates are
    # separately checked so a changed fixture cannot silently bypass it.
    if signed(s[0x4c1])>=0 and signed(s[0x1277]-1)>=0 and 16<=signed(s[0xdeb])<48:
        raise ValueError('unsupported late AI recovery branch')
    return s


def completed_rotation(state):
    """Primary rotation tracking in $82:9A53..9D97; returns reward event codes.

    Track quarter turns on active motion phases. Landing rounds three quarters
    up to one completed turn. Only the ordinary jump/rotation domain is
    recovered here; wall rides, flips and failed stunts reject explicitly.
    """
    s=dict(state);rider=s[0xff9];events=[]
    fields=[0x1203+rider,0x1207+rider,0x120b+rider,0x120f+rider]
    forward,reverse,quarter_forward,quarter_reverse=fields
    if abs(signed(s[0xf17]))==31 or s[0x433+rider] or s[0x1249]:
        raise ValueError('unsupported wall/flip rotation tracker')
    if not s[0xf55] and signed(s[0xf33]-2)>=0:
        if s[0xf33]==2 or not s[0x136b+rider]:
            rotation=s[0xf57]&255
            if rotation&128:rotation-=256
            s[0xf67]=((s[0xf53]-rotation)&63)>>4
            s[0x33f+rider]=s[0xf51]
            s[0x136b+rider]=1
            for a in fields:s[a]=0
        else:
            current=s[0xf53]>>4;previous=s[0xf67]
            if current!=previous:
                if current==3:increasing=previous==2
                elif previous==3:increasing=current!=2
                else:increasing=current>previous
                quarter,opposite,total=(quarter_forward,quarter_reverse,forward) if increasing else (quarter_reverse,quarter_forward,reverse)
                count=(s[quarter]+1)&65535
                if signed(count-4)>=0:
                    s[total]=(s[total]+1)&65535;count=0
                s[quarter]=count;s[opposite]=0
            s[0xf67]=current
    else:
        if s[0xf5d] or s[0xf6b] or s[0x42b+rider] or s[0x42f+rider]:
            raise ValueError('unsupported failed/combined stunt classification')
        for turns,quarters,reflected_code,normal_code in [(forward,quarter_forward,0,4),(reverse,quarter_reverse,4,0)]:
            if s[quarters]==3:s[turns]=(s[turns]+1)&65535
            count=min(s[turns],4)
            if count:events.append(count+(reflected_code if s[0x33f+rider] else normal_code))
        s[0xf67]=s[0xf6b]=s[0x136b+rider]=0
        for a in fields:s[a]=0
    return s,events


def reward_queue_step(state, event_codes, reward_words, event_classes):
    """Opponent queue $81:C59C/C219 and its gameplay reward subset.

    Called after motion publications, before contact. Caller already applied
    both per-rider common-counter ticks to the cooldown. Static event class and
    signed reward words come from ROM, never fitted to the movement series.
    """
    s=dict(state)
    for code in event_codes:
        if s[0xd13] != s[0xd11]:
            s[0xceb+s[0xd13]]=code
            s[0xd13]=(s[0xd13]+1)&31
    if s[0xca7]:return s
    next_read=(s[0xd11]+1)&31
    if next_read==s[0xd13]:
        s[0xca7]=10
        return s
    s[0xd11]=next_read
    event=s[0xceb+next_read]&255
    if not 1<=event<0x48:raise ValueError('unsupported queue event domain')
    if event_classes[event-1] != 255:
        weight=s[0x7e2102+event-1]
        if not weight:raise ValueError('unsupported exhausted reward weight')
        s[0x770825]=(s[0x770825]+weight)&65535
        s[0x7e2102+event-1]=max(weight>>1,1)
        amount=signed(reward_words[event-1])
        # Original CMP #$FFFF / BPL uses the sign of word subtraction.
        if signed(s[0x11db]+1)<0:s[0x11db]=0
        if amount>=0:
            s[0x11db]=(s[0x11db]+amount)&65535
            s[0x11e1]=(s[0x11e1]+amount)&65535
    remaining=(s[0xd13]-s[0xd11]-1)&31
    s[0xca7]=max(5,40-4*remaining)
    return s


def throttle_update(state):
    """Primary/release branch of $82:98CF..9A52, including brake-release launch."""
    s=dict(state);rider=s[0xff9]
    if s[0x547+rider]:raise ValueError('unsupported throttle inhibit')
    s[0xe7b]=1
    if signed(s[0xf33]-2)>=0 or s[0xf17] in (0xffe1,31) or s[0xf5d]:
        s[0xf5f]=0;s[0xf63]=0
    else:
        if s[0xf19] and abs(signed(s[0xfa9]))>=16:
            raise ValueError('unsupported moving brake')
        axis=s[0xf21]&255
        if axis==1:
            s[0xf5f]=0;s[0xf63]=0
        elif axis==2:
            if s[0xf13]&0x8000 or s[0x42b+rider]:raise ValueError('unsupported throttle surface mode')
            s[0xfa9]=(s[0xfa9]+(s[0xf3b] or 24))&65535
            limit=(max(0,signed(s[0x11d7]))+s[0x11d1]+s[0x11f1])&65535
            candidate=(s[0xf5f]+16)&65535
            if signed(candidate-limit)<0:s[0xf5f]=candidate
            if signed(s[0xf73]-4)<0:
                if s[0xc77+rider]!=4:s[0xc77+rider]=(s[0xc77+rider]+1)&65535
                s[0xf3d]=s[0xc77+rider];s[0xe7b]=0
            if s[0xf19]:
                s[0xfa9]=0
                if s[0xfb1] or s[0xf45] or s[0xf61]:raise ValueError('unsupported stationary brake mode')
                if s[0xf5f]:s[0xf63]=1
            elif s[0xf65]:
                if s[0xf5f]:
                    s[0xfa9]=(s[0xfa9]+s[0xf5f])&65535
                    s[0xf5f]=0;s[0x11f1]=256;s[0xf63]=0
                else:s[0xf63]=0
        else:raise ValueError('unrecovered horizontal throttle direction')
    s[0xf65]=s[0xf19]
    return s


def stationary_animation_override(state):
    """$82:A069..A0B6; active-phase wheel motion when airborne or stationary."""
    s=dict(state)
    if signed(s[0xf33]-2)<0 and any(signed(s[a]-2)>=0 for a in [0xf6d,0xf6f,0xf71,0xf73]):return s
    axis=s[0xf21]&255
    if axis!=1:
        value=2 if axis<1 else -2
        s[0xf3d]=(-value if s[0xf51] else value)&65535
    return s


def common_motion_reset(state):
    """Primary common pre-update $81:8592..8704, excluding global cooldowns."""
    s=dict(state)
    unsupported=[0xf29,0xf2f,0xf35,0xf37,0xf45,0xf47,0xf49,0xf59,0x359+s[0xff9]]
    if any(s[a] for a in unsupported):raise ValueError('unrecovered common motion timer/mode')
    for a in [0xf5b,0xf35,0xf23,0xf27,0xf3b,0xf3d,0xf3f,0xf41,0xf2d,0x11f1,0xfa7,0xf4b,0xf49,0xfb1,0xf39]:s[a]=0
    return s
