class Position(object):
    """Wrapper object around an array of two integers to hold the
    carets position in the document. This can be useful when
    refering to a position in the document in our errors. For
    instance:

        MSG = {
            'E101': 'no more backticks after {0} to match',
        }

        NodeParser.msg('E101', parser.pos, [Position(pos)])

    In this way when an error is display it will display the position
    in whichever format the `Position` object has stored.
    """

    def __init__(self, pos, fmt='{0}:{1:2}'):
        self.line = pos[0]
        self.column = pos[1]
        self.fmt = fmt

    def __str__(self):
        return self.fmt.format(self.line, self.column)

    def __repr__(self):
        return repr([self.line, self.column])

    def set_format(self, fmt='{0}:{1:2}'):
        """Set the display format. To reset to the default value
        call with no arguments.
        """
        self.fmt = fmt

    def shift(self, delta):
        """Shift the position by the amount specified by delta."""
        self.line += delta[0]
        self.column += delta[1]
