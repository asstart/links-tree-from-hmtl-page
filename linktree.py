import link_parser
import click


@click.command()
@click.option("--link", help="link to parse")
@click.option("--file", default="linktree.md", help="path to the file with result")
def main(link, file):
    link_parser.make_links_tree_file(link, file)


if __name__ == "__main__":
    main()
