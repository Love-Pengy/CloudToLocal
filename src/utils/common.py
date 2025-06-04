def get_diff_count(in1, in2):
    """
        Get Amount Of Characters That Differ Between Two Strings
            Taking Into Account Position

        Args:
            in1 (str)
            in2 (str)

        Returns:
            Amount Of Characters That Are Different
    """
    if (len(in1) < len(in2)):
        str1 = in1
        str2 = in2
    else:
        str1 = in2
        str2 = in1

    count = 0
    for index, char in enumerate(str1):
        if (char != str2[index]):
            count += 1

    count += len(str2) - (index+1)
    return (count)


def sanitize_string(string):
    """Sanitize String For Usage In Filename
        replacing / with division slash
        and \0 with reverse solidus and 0"""
    return (string.replace('/', '∕').replace('\0', '\\'))
