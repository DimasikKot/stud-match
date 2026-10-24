export const ButtonPage = ({
  onClick,
  isLoading,
}: {
  onClick: () => void;
  isLoading?: boolean;
}) => {
  return (
    <div className="sticky sm:top-52 lg:top-23 self-start">
      <div className="absolute bg-white -left-18 rounded-3xl select-none">
        <div>
          <button onClick={() => window.history.back()}>
            <div
              className="w-12 h-12 border border-gray-200 hover:bg-gray-100 active:bg-gray-200 rounded-3xl
        flex items-center justify-center text-4xl text-gray-700 hover:text-gray-900 transition-colors cursor-pointer"
            >
              <span className="material-icons">arrow_back</span>
            </div>
          </button>
        </div>

        <div>
          <button onClick={onClick}>
            <div
              className="mt-4 w-12 h-12 border border-gray-200 hover:bg-gray-100 active:bg-gray-200 rounded-3xl
        flex items-center justify-center text-4xl text-gray-700 hover:text-gray-900 transition-colors cursor-pointer"
            >
              <span className="material-icons">arrow_upward</span>
            </div>
          </button>
        </div>

        {isLoading != undefined && (
          <div
            className="mt-4 w-12 h-12 border border-gray-200 rounded-3xl
          flex items-center justify-center text-4xl text-gray-700 transition-colors"
          >
            <span
              className={`material-icons ${isLoading ? "animate-spin" : ""}`}
            >
              {isLoading ? "refresh" : "done"}
            </span>
            {/* <span className="material-icons">task_alt</span> */}
          </div>
        )}
      </div>
    </div>
  );
};
