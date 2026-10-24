export const RightPanel = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="sticky sm:top-52 lg:top-23 self-start">
      <div className="absolute right-0 top-0 max-h-160 w-80 translate-x-86">
        <div
          className="border border-gray-300 rounded-2xl h-full w-80 overflow-clip bg-white"
          onClick={(event) => event.stopPropagation()}
          onScroll={(event) => event.stopPropagation()}
        >
          <div className="py-2 w-80 max-h-160 overflow-auto">{children}</div>
        </div>
      </div>
    </div>
  );
};
