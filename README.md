# unitguard

The most expensive errors in quantitative models are not subtle. Someone adds
kWh to MWh. Someone reports tonnes of carbon as tonnes of CO2 and is off by a
factor of 3.67. Someone divides by an intensity that was per unit of revenue,
not per unit of output. None of these throw an exception; they produce a number
that looks entirely reasonable and is wrong.

`unitguard` makes dimensions explicit and checks them. Quantities carry units,
arithmetic enforces dimensional consistency, and conversions that are
genuinely ambiguous raise rather than resolve.

It comes out of energy and emissions modelling, where the unit zoo is worst,
but the failure mode is universal.

Each tool lives in its own folder with its own README and its own tests, and
leans on the Python standard library unless a dependency genuinely earns its
place.

## Layout

```
projects/
  NNN-project-name/
    README.md          what it does, how to run it, what it is not
    <package>/         the implementation
    tests/             python3 -m unittest discover -s tests -t .
    examples/          a working input file
    pyproject.toml     dependencies, if any
```

## Roadmap

See [BACKLOG.md](BACKLOG.md).

## Licence

MIT, per project. See [LICENSE](LICENSE).
