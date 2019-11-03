
def enum_or(raw_elements):
    elements = list(raw_elements)
    if len(elements) == 1:
        return str(elements[0])
    else:
        return ', '.join(str(el) for el in elements[0:-1]) + ' or ' + str(elements[-1])

