from nml import generic
from nml.actions import action2, action1

class Action2Real(action2.Action2):
    def __init__(self, feature, name, loaded_list, loading_list):
        action2.Action2.__init__(self, feature, name)
        self.loaded_list = loaded_list
        self.loading_list = loading_list

    def write(self, file):
        size = 2 + 2 * len(self.loaded_list) + 2 * len(self.loading_list)
        action2.Action2.write_sprite_start(self, file, size)
        file.print_byte(len(self.loaded_list))
        file.print_byte(len(self.loading_list))
        file.newline()
        for i in self.loaded_list:
            file.print_word(i)
        file.newline()
        for i in self.loading_list:
            file.print_word(i)
        file.newline()
        file.end_sprite()

real_action2_alias = {
    'loaded': (0, [0x00, 0x01, 0x02, 0x03]),  #vehicles
    'loading': (1, [0x00, 0x01, 0x02, 0x03]), #vehicles
    'default': (0, [0x05, 0x0B, 0x0D, 0x10]), #canals, cargos, railtypes, airports
}

def get_real_action2s(spritegroup, feature):
    loaded_list = []
    loading_list = []
    actions = []

    if feature not in action2.features_sprite_group:
        raise generic.ScriptError("Sprite groups that combine sprite sets are not supported for feature '%02X'." % feature, spritegroup.pos)

    if len(spritegroup.spriteview_list) == 0:
        raise generic.ScriptError("Sprite groups require at least one sprite set.", spritegroup.pos)

    # First make sure that all referenced real sprites are put in a single action1
    actions.extend(action1.add_to_action1(spritegroup.used_sprite_sets, feature, spritegroup.pos))

    for view in spritegroup.spriteview_list:
        if view.name.value not in real_action2_alias: raise generic.ScriptError("Unknown sprite view type encountered in sprite group: " + view.name.value, view.pos)
        type, feature_list = real_action2_alias[view.name.value]
        if feature not in feature_list:
            raise generic.ScriptError("Sprite view type '%s' is not supported for feature '%02X'." % (view.name.value, feature), view.pos)
        if feature in (0x05, 0x0B, 0x0D, 0x10):
            generic.print_warning("Sprite groups for feature %02X will not be supported in the future, as they are no longer needed. Directly refer to sprite sets instead." % feature, view.pos)

        for set_ref in view.spriteset_list:
            spriteset = action2.resolve_spritegroup(set_ref.name)
            action1_index = action1.get_action1_index(spriteset)
            if type == 0: loaded_list.append(action1_index)
            else: loading_list.append(action1_index)

    actions.append(Action2Real(feature, spritegroup.name.value + (" - feature %02X" % feature), loaded_list, loading_list))
    spritegroup.set_action2(actions[-1], feature)
    return actions

def create_spriteset_actions(spritegroup):
    """
    Create action2s for directly-referenced sprite sets

    @param spritegroup: Spritegroup to create the sprite sets for
    @type spritegroup: L{ASTSpriteGroup}

    @return: Resulting list of actions
    @rtype: C{list} of L{BaseAction}
    """
    action_list = []
    # Iterate over features first for more efficient action1s
    for feature in spritegroup.feature_set:
        if len(spritegroup.used_sprite_sets) != 0 and feature not in action2.features_sprite_group:
            raise generic.ScriptError("Directly referring to sprite sets is not possible for feature %02X" % feature, spritegroup.pos)
        for spriteset in spritegroup.used_sprite_sets:
            if spriteset.has_action2(feature): continue
            action_list.extend(action1.add_to_action1([spriteset], feature, spritegroup.pos))
            action1_index = action1.get_action1_index(spriteset)
            real_action2 = Action2Real(feature, spriteset.name.value + (" - feature %02X" % feature), [action1_index], [action1_index] if feature <= 0x03 else [])
            action_list.append(real_action2)
            spriteset.set_action2(real_action2, feature)
    return action_list
