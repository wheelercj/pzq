try:
    from app import main
except ImportError:
    from zq.app import main

if __name__ == "__main__":
    main()
