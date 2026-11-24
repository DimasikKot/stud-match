export const IconSvgUI = ({
  src,
  className: customClassName,
}: {
  src: string;
  className?: string;
}) => {
  return (
    <div className="flex items-center">
      <span
        aria-hidden="true"
        className={`inline-block shrink-0 bg-current h-6 w-6 ${customClassName}`}
        style={{
          maskImage: `url("${src}")`,
          WebkitMaskImage: `url("${src}")`,
          maskSize: "contain",
          WebkitMaskSize: "contain",
          maskRepeat: "no-repeat",
          WebkitMaskRepeat: "no-repeat",
          maskPosition: "center",
          WebkitMaskPosition: "center",
        }}
      />
    </div>
  );
};
