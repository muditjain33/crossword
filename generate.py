from os import remove
import sys

from PIL.Image import NONE

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
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        
        for key,value in self.domains.items():
            k=key.length
            l=[]
            for i in value:
                if(len(i)!=k):
                    l.append(i)
            for i in l:
                self.domains[key].remove(i)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        if self.crossword.overlaps[x,y]==None:
            return False
        ai,bj=self.crossword.overlaps[x,y]
        l=[]
        for i in self.domains[x]:
            flag=0
            for j in self.domains[y]:
                if(i[ai]==j[bj]):
                    flag=1
                    break
            if(flag==0):
                l.append(i)
        if(len(l)==0):
            return False
        for i in l:
            self.domains[x].remove(i)
        return True


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if(arcs==None):
            narcs=[]
            for key,value in self.crossword.overlaps.items():
                narcs.append(key)
            arcs=narcs
        for i,j in arcs:
            if(self.revise(i,j)):
                if(len(self.domains[i])==0):
                    return False
                for z in self.crossword.neighbors(i):
                    if(z==j):
                        continue
                    else:
                        arcs.append((z,i))
        return True
        



    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for k,v in self.domains.items():
            if(k not in assignment):
                return False
        for i,j in assignment.items():
            if(j==None):
                return False
            if(len(j)<=0):
                return False
        return True
        # raise NotImplementedError

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # all values are distinct
        # every value is the correct length
        # no conflicts between neighboring variables
        l=[]
        for key,value in assignment.items():
            if(key.length!=len(value)):
                return False
            if(value in l):
                return False
            l.append(value)
            for i in self.crossword.neighbors(key):
                if(i not in assignment):
                    continue
                if self.crossword.overlaps[key,i]!=None:
                    ai,bj=self.crossword.overlaps[key,i]
                    if(str(assignment[key])[ai]!=str(assignment[i])[bj]):
                        return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        values=self.domains[var]
        d=dict()
        
        we=self.crossword.neighbors(var)
        for i,k in assignment.items():
            we.discard(i)
        
        for i in values:
            d[i]=0
            ans=0
            for j in we:
                ai,bj=self.crossword.overlaps[var,j]
                jvalues=self.domains[j]
                for k in jvalues:
                    if(i[ai]!=k[bj]):
                        ans+=1
            d[i]+=ans

        sort_by_value = dict(sorted(d.items(), key=lambda item: item[1]))
        
        l=[]
        for i,j in sort_by_value.items():
            l.append(i)


        return l

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        d=dict()
        for key,value in self.domains.items():
            if(key not in assignment):
                d[key]=len(value)
        sort_by_value = dict(sorted(d.items(), key=lambda item: item[1]))
        l=list(sort_by_value.values())
        l1=list(sort_by_value.keys())
        a=l[0]
        counter=0
        for i in l:
            if(a==i):
                counter+=1
        if(counter==1):
            return l1[0]
        else:
            l3=[]
            for i in range(0,counter):
                l3.append(l1[i])
            d1=dict()
            for i in l3:
                d1[i]=len(self.crossword.neighbors(i))
            by_value = dict(sorted(d.items(), key=lambda item: item[1]))
            l4=list(sort_by_value.keys())
            return l4[-1]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if(self.assignment_complete(assignment)==True):
            return assignment
        var=self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var,assignment):
            assignment[var]=value
            if(self.consistent(assignment)):
                result=self.backtrack(assignment)
                if(result!=False):
                    return result
            del assignment[var]
        return False


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
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
