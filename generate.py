from collections import deque
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self, creator):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict(), creator)

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable, words in self.domains.items():
            self.domains[variable] = [word for word in words if len(word) == variable.length ]

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        
        cross = self.crossword.overlaps[x,y]
        isRevised = False

        if cross != None:
            # words = [word for word in self.domains.get(x) if word[cross[0]] == self.domains.get(y)[0][cross[1]]]
            # print(words)
            xWords = self.domains.get(x)
            yWords = self.domains.get(y)
            xCross, yCross = cross
            newWords = set()

            for xWord in xWords:
                for yWord in yWords:
                    if xWord != yWord and xWord[xCross] == yWord[yCross]:
                        newWords.add(xWord)
            
            isRevised = len(xWords) > len(newWords)
            self.domains[x] = newWords
            
            if isRevised:
                self.domains[x] = newWords
        
        return isRevised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = self.domains

        arc_queue = deque()
        arc_queue.extend(arcs.keys())

        while arc_queue:
            current_variable = arc_queue.pop()
            current_words = self.domains.get(current_variable)
            # iterate over current_variable neighbors
            neighbors = self.crossword.neighbors(current_variable)
            for another_variable in neighbors:
                if current_variable == another_variable:
                    continue
                isRevised = self.revise(another_variable, current_variable)
                another_words = self.domains.get(another_variable)

                if isRevised:
                    #check if current words size is 0
                    if len(another_words) == 0:
                        return False
                    # append all current_variable neighbors 
                    arc_queue.append(another_variable)    
                              
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return len(assignment) == len(self.domains);

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        result = self.ac3(assignment) and (assignment == None or len(assignment.values()) == len(set(assignment.values())))
        return result

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        unassigned = {k: v for k, v in self.domains.items() if k not in assignment}
        selected_key = None  
        min_val_size = 10000 

        for k, v in unassigned.items():
            if min_val_size > len(v):
                selected_key = k 
                min_val_size = len(v)
            elif min_val_size == len(v):
                k_neighbors = self.crossword.neighbors(k)
                selected_neighbors = self.crossword.neighbors(selected_key)
                selected_key = k if len(k_neighbors) > len(selected_neighbors) else selected_key
                
        return selected_key 

    def backtrack(self, assignment, creator):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment       
        
        unassigned_var = self.select_unassigned_variable(assignment)

        for value in self.domains.get(unassigned_var):
            self.consistent(assignment)
            if value in self.domains.get(unassigned_var): # problem here. We tool "value" before sorting
                assignment[unassigned_var] = value 
                self.domains[unassigned_var] = {value}
                creator.save(assignment, 'output.png')
                result = self.backtrack(assignment, creator)
                if result != None:
                    return result 
                del assignment[unassigned_var]
        

        return None 


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve(creator)

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
